from gaze_audit.exact_intervals import stratified_binary_interval


def test_census_positive_boundary_is_the_exact_integer_population_grid_point():
    sizes = [1938, 1401, 6960, 17]
    counts = [1938, 1401, 770, 17]
    successes = [262, 99, 0, 2]
    truth = 363 / 10316
    low, high = stratified_binary_interval(successes, counts, sizes)
    assert low == truth
    assert low <= truth <= high
