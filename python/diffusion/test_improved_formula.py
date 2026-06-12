"""改进高斯烟羽公式的回归检查。

运行：
    python -m diffusion.test_improved_formula
"""

from __future__ import annotations

import sys

import numpy as np

from diffusion.gaussian_plume import (
    corrected_dispersion_coefficients,
    particle_rebound_alpha,
    steady_plume_mass_conc,
)


def main() -> int:
    distances = np.array([50.0, 100.0, 200.0, 400.0, 800.0])
    classic = steady_plume_mass_conc(
        80.0,
        3.5,
        distances,
        0.0,
        1.5,
        1.0,
        "D",
        False,
    )
    improved = steady_plume_mass_conc(
        80.0,
        3.5,
        distances,
        0.0,
        1.5,
        1.0,
        "D",
        False,
        model_variant="improved",
        diffusion_correction_k=1.0,
        reflection_alpha=particle_rebound_alpha(rebound_eta=0.4),
    )
    near_classic = steady_plume_mass_conc(
        80.0,
        3.5,
        distances,
        0.0,
        1.5,
        1.0,
        "D",
        False,
        model_variant="classic",
        diffusion_correction_k=1.0,
        reflection_alpha=0.2,
    )
    sy_classic, sz_classic = corrected_dispersion_coefficients(distances, "D", False, 3.5, 1.0, "classic")
    sy_improved, sz_improved = corrected_dispersion_coefficients(distances, "D", False, 3.5, 1.0, "improved")

    failures: list[str] = []
    if not np.all(np.isfinite(improved)) or np.any(improved < 0):
        failures.append("改进模型浓度必须有限且非负")
    if np.allclose(classic, improved):
        failures.append("改进模型应当不同于经典基线")
    if not np.allclose(classic, near_classic):
        failures.append("经典模式必须忽略仅用于改进模型的修正参数")
    if not np.all(np.asarray(sy_improved) > np.asarray(sy_classic)):
        failures.append("K=1 时改进 sigma_y 应当更宽")
    if not np.all(np.asarray(sz_improved) > np.asarray(sz_classic)):
        failures.append("在演示风速/K 设置下，改进 sigma_z 应当更宽")

    print("改进高斯公式回归检查")
    print(f"经典模型 mg/m3 : {(np.asarray(classic) * 1000).round(6).tolist()}")
    print(f"改进模型 mg/m3: {(np.asarray(improved) * 1000).round(6).tolist()}")
    print(f"alpha(eta=0.4): {particle_rebound_alpha(rebound_eta=0.4):.6f}")
    print("结果:", "失败" if failures else "通过")
    for failure in failures:
        print(f" - {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
