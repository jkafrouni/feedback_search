

def mock_feedback(query_results):
    for i, result in enumerate(query_results):
        query_results[i].update({'relevant': True if i is 0 else False})
    return query_results
