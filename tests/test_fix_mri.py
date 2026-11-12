"""Regression tests: MRI (NIfTI) loading works; the super-resolution entry, whose format was never defined, is gone."""
import numpy as np
import pytest

nib = pytest.importorskip("nibabel")
pytest.importorskip("skimage")

from wireframe import Wireframe  # noqa: E402


def sphere_volume(n=32, radius=10.0, frames=0):
    g = np.mgrid[:n, :n, :n].astype(float) - (n - 1) / 2
    vol = np.clip(radius + 0.5 - np.sqrt((g ** 2).sum(axis=0)), 0, 1) * 100.0  # 100 inside, 0 outside
    return np.stack([vol] * frames, axis=-1) if frames else vol


@pytest.mark.parametrize("frames", [0, 3])
def test_load_mri_isosurface_in_world_mm(tmp_path, frames):
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    affine[:3, 3] = [-31.0, 5.0, 12.0]  # voxel (15.5, 15.5, 15.5) -> world (0, 36, 43) mm
    path = tmp_path / ("sphere.nii.gz" if frames else "sphere.nii")
    nib.save(nib.Nifti1Image(sphere_volume(frames=frames).astype(np.float32), affine), str(path))
    w = Wireframe.load_mri(path)
    assert len(w.vertices) > 100 and w.faces.shape[1] == 3
    r = np.linalg.norm(w.vertices - np.array([0.0, 36.0, 43.0]), axis=1)
    assert np.allclose(r, 20.0, atol=1.5)  # 10-voxel radius at 2 mm per voxel


def test_viewer_loads_mri_and_has_no_super_resolution(tmp_path, monkeypatch):
    pytest.importorskip("PyQt5")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance() or QApplication([])  # noqa: F841
    import wireframe_viewer as wv
    errors = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: errors.append(a[2]))
    v = wv.WireframeViewer()
    v.animation_timer.stop()
    path = tmp_path / "s.nii"
    nib.save(nib.Nifti1Image(sphere_volume(16, 5).astype(np.float32), np.eye(4)), str(path))
    v.on_shape_loaded(("mri", str(path)))  # used to fail: Wireframe.load_mri did not exist
    assert errors == [] and len(v.scene.objects) == 1
    assert not hasattr(v.shape_loader, "load_sr_button")
    with pytest.raises(ValueError):
        v.create_wireframe("super_resolution", "x.txt")
