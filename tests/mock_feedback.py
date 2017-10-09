
mock_feedbacks = {
    'jaguar': {'relevant': [0, 2, 3, 4, 8, 9], 'non-relevant': [1, 5, 6, 7]},
    'lion': {'relevant': [0, 2, 3, 4, 5, 9], 'non-relevant': [1, 6, 7, 8]},
    'brin': {'relevant': [0, 6, 8, 9], 'non-relevant': [1, 2, 3, 4, 5, 7]},
    'bulls': {'relevant': [0, 1, 2, 3, 4, 5, 7], 'non-relevant': [6, 8, 9]}
    }

def mock_feedback(query_results, query=None):
    if query is not None:
        for i in mock_feedbacks[query]['relevant']:
            query_results[i].update({'relevant': True})
        for i in mock_feedbacks[query]['non-relevant']:
            query_results[i].update({'relevant': False})
    else:
        for i, result in enumerate(query_results):
            query_results[i].update({'relevant': True if i is 0 else False})
        return query_results
