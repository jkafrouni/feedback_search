

def mock_feedback(query_results, query=None):
    if query == 'jaguar':
        for i in [0, 2, 3, 4, 8, 9]:
            query_results[i].update({'relevant': True})
        for i in [1, 5, 6, 7]:
            query_results[i].update({'relevant': False})
    else:
        for i, result in enumerate(query_results):
            query_results[i].update({'relevant': True if i is 0 else False})
        return query_results
