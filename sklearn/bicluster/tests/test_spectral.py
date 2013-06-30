"""Testing for Spectral Biclustering methods"""

from sklearn.utils import check_random_state

import numpy as np

from sklearn.utils.testing import assert_equal
from sklearn.utils.testing import assert_almost_equal
from sklearn.utils.testing import assert_array_equal
from sklearn.utils.testing import assert_array_almost_equal

from sklearn.bicluster.spectral import \
    SpectralBiclustering, \
    _scale_preprocess, _bistochastic_preprocess, \
    _log_preprocess, _fit_best_piecewise, \
    _project_and_cluster


def test_spectral_biclustering_dhillon():
    """Test Dhillon's Spectral CoClustering on a simple problem."""
    S = np.zeros((30, 30))
    S[0:10, 0:10] = 1
    S[10:20, 10:20] = 2
    S[20:30, 20:30] = 3

    model = SpectralBiclustering(random_state=0, n_clusters=3,
                                 method='dhillon')
    model.fit(S)

    # ensure every row and column is in exactly one bicluster, and
    # that each bicluser has the expected number of elements.
    assert_equal(model.rows_.shape, (3, 30))
    assert_array_equal(model.rows_.sum(axis=0), np.ones(30))
    assert_array_equal(model.rows_.sum(axis=1), np.repeat(10, 3))
    assert_array_equal(model.columns_.sum(axis=0), np.ones(30))
    assert_array_equal(model.columns_.sum(axis=1), np.repeat(10, 3))


def _test_spectral_biclustering_kluger(noise=0.0):
    """Test Kluger methods on a checkerboard dataset.

    Parameters
    ----------
    noise : integer, optional, default=0.0
        Standard deviation of gaussian noise to be added to the
        data.

    """
    # make a checkerboard array
    row_vector = [1] * 10 + [3] * 10 + [5] * 10
    col_vector = [2] * 10 + [4] * 10 + [6] * 10
    S = np.outer(row_vector, col_vector).astype(np.float64)

    if noise > 0:
        generator = check_random_state(0)
        S += generator.normal(0, noise, S.shape).astype(np.float64)

    for method in ('scale', 'bistochastic', 'log'):
        model = SpectralBiclustering(random_state=0, n_clusters=(3, 3),
                                     method=method)
        model.fit(S)

        # ensure every row and column is in exactly three biclusters,
        # and that each bicluser has the expected number of elements.
        assert_equal(model.rows_.shape, (9, 30))
        assert_array_equal(model.rows_.sum(axis=0), np.repeat(3, 30))
        assert_array_equal(model.rows_.sum(axis=1), np.repeat(10, 9))
        assert_equal(model.columns_.shape, (9, 30))
        assert_array_equal(model.columns_.sum(axis=0), np.repeat(3, 30))
        assert_array_equal(model.columns_.sum(axis=1), np.repeat(10, 9))


def test_spectral_biclustering_kluger_without_noise():
    _test_spectral_biclustering_kluger(noise=0)


def test_spectral_biclustering_kluger_with_noise():
    _test_spectral_biclustering_kluger(noise=0.5)


def _do_scale_test(scaled):
    """Ensures that rows sum to one constant, and columns to another
    constant.

    """
    row_sum = scaled.sum(axis=1)
    col_sum = scaled.sum(axis=0)
    assert_array_almost_equal(row_sum, np.tile(row_sum.mean(), 100),
                              decimal=1)
    assert_array_almost_equal(col_sum, np.tile(col_sum.mean(), 100),
                              decimal=1)


def _do_bistochastic_test(scaled):
    """Ensure that rows and columns sum to the same constant."""
    _do_scale_test(scaled)
    assert_almost_equal(scaled.sum(axis=0).mean(),
                        scaled.sum(axis=1).mean(),
                        decimal=1)


def test_scale_preprocess():
    generator = check_random_state(0)
    x = generator.rand(100, 100)
    scaled, _, _ = _scale_preprocess(x)
    _do_scale_test(scaled)


def test_bistochastic_preprocess():
    generator = check_random_state(0)
    x = generator.rand(100, 100)
    scaled = _bistochastic_preprocess(x)
    _do_bistochastic_test(scaled)


def test_log_preprocess():
    # adding any constant to a log-scaled matrix should make it
    # bistochastic
    generator = check_random_state(0)
    x = generator.rand(100, 100)
    scaled = _log_preprocess(x) + 1
    _do_bistochastic_test(scaled)


def test_fit_best_piecewise():
    vectors = np.array([[0, 0, 0, 1, 1, 1],
                        [2, 2, 2, 3, 3, 3],
                        [0, 1, 2, 3, 4, 5],])
    best = _fit_best_piecewise(vectors, k=2, n_clusters=2,
                               random_state=0, n_init=10)
    assert_array_equal(best, vectors[0:2])


def test_project_and_cluster():
    data = np.array([[1, 1, 1,],
                     [1, 1, 1,],
                     [3, 6, 3,],
                     [3, 6, 3,]])
    vectors = np.array([[1, 0,],
                        [0, 1,],
                        [0, 0,]])
    labels = _project_and_cluster(data, vectors, n_clusters=2,
                                  random_state=0, n_init=10)
    assert_array_equal(labels, [0, 0, 1, 1])