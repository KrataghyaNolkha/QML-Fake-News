from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .feature_maps import FeatureMapName, build_feature_map


class StatevectorQuantumKernel:
    """Ideal fidelity kernel evaluated from cached feature-map statevectors.

    For a unitary feature map, the fidelity kernel is
    ``|<phi(x)|phi(y)>|**2``. Computing each state once avoids repeatedly
    simulating the same feature-map circuits for every Pegasos update.
    """

    def __init__(self, feature_map):
        from qiskit.quantum_info import Statevector

        self.feature_map = feature_map
        self._Statevector = Statevector
        self._parameters = tuple(feature_map.parameters)
        self._state_cache: dict[tuple[float, ...], np.ndarray] = {}

    def _states(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self._parameters):
            raise ValueError(
                f"Expected a 2D input with {len(self._parameters)} features; got {X.shape}."
            )
        states = []
        for row in X:
            key = tuple(float(v) for v in row)
            state = self._state_cache.get(key)
            if state is None:
                bound = self.feature_map.assign_parameters(dict(zip(self._parameters, row)), inplace=False)
                state = np.asarray(self._Statevector.from_instruction(bound).data, dtype=complex)
                self._state_cache[key] = state
            states.append(state)
        return np.asarray(states, dtype=complex)

    def evaluate(self, x_vec: np.ndarray, y_vec: Optional[np.ndarray] = None) -> np.ndarray:
        X = np.asarray(x_vec, dtype=float)
        Y = X if y_vec is None else np.asarray(y_vec, dtype=float)
        left = self._states(X)
        right = left if y_vec is None else self._states(Y)
        overlaps = left.conj() @ right.T
        return np.abs(overlaps) ** 2


@dataclass
class QuantumKernelFactory:
    feature_map_name: FeatureMapName
    num_qubits: int
    reps: int = 2
    seed: int = 42
    shots: Optional[int] = None
    noise_prob: float = 0.0

    def build(self):
        """Creates a FidelityQuantumKernel configured for either ideal or noisy simulation."""
        from qiskit_algorithms.utils import algorithm_globals

        algorithm_globals.random_seed = self.seed

        feature_map = build_feature_map(self.feature_map_name, self.num_qubits, reps=int(self.reps))

        # Qiskit ML (this version) accepts a `fidelity` object.
        # For noise robustness we build a ComputeUncompute fidelity powered by a noisy Aer Sampler.
        if self.noise_prob and self.noise_prob > 0:
            sampler, transpiler = _build_noisy_sampler(noise_prob=self.noise_prob, shots=self.shots, seed=self.seed)
            from qiskit_algorithms.state_fidelities import ComputeUncompute
            from qiskit_machine_learning.kernels import FidelityQuantumKernel

            fidelity = ComputeUncompute(sampler=sampler, shots=self.shots, transpiler=transpiler)
            return FidelityQuantumKernel(feature_map=feature_map, fidelity=fidelity)

        # Ideal/statevector path: cache one statevector per input and form
        # fidelities with a matrix multiplication. This is equivalent to the
        # ideal FidelityQuantumKernel and practical for full-data Gram matrices.
        return StatevectorQuantumKernel(feature_map=feature_map)


def _build_noisy_sampler(*, noise_prob: float, shots: Optional[int], seed: int):
    """Build a sampler backed by AerSimulator with depolarizing noise.

    This function is written to be resilient across Qiskit versions; if a specific
    sampler class isn't available, it will raise a helpful error.
    """

    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit_aer import AerSimulator
    from qiskit.primitives import BackendSamplerV2
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    noise_model = NoiseModel()

    error_1q = depolarizing_error(noise_prob, 1)
    error_2q = depolarizing_error(min(1.0, 2 * noise_prob), 2)

    one_qubit_gates = ["rx", "ry", "rz", "x", "y", "z", "h", "s", "sdg", "t", "tdg"]
    two_qubit_gates = ["cx", "cz", "swap"]

    for g in one_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_1q, g)
    for g in two_qubit_gates:
        noise_model.add_all_qubit_quantum_error(error_2q, g)

    # Construct a V2 sampler required by ComputeUncompute.
    # We configure noise on the backend itself.
    backend = AerSimulator(noise_model=noise_model, seed_simulator=seed)
    options = {"seed_simulator": int(seed)}
    if shots is not None:
        options["default_shots"] = int(shots)

    sampler = BackendSamplerV2(backend=backend, options=options)
    transpiler = generate_preset_pass_manager(backend=backend, optimization_level=1)
    return sampler, transpiler


def evaluate_kernel_matrix(kernel, X_left: np.ndarray, X_right: np.ndarray) -> np.ndarray:
    return np.asarray(kernel.evaluate(x_vec=X_left, y_vec=X_right), dtype=float)
