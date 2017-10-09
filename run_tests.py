from tests import constants_tuning

with open('tests/parameters_tuning.txt', 'a') as outfile:
    outfile.write('\n\n************** NEW TEST SESSION ***************\n\n')

# for i in range(11):
#     title_weight = i/10
#     for j in range(0, 11 - i):
#         summary_weight = j/10
#         content_weight = (10 - i - j)/10
        
#         constants_tuning.test_constants(
#             # "bulls" ,
#             {'title_weight': title_weight, "summary_weight": summary_weight, "content_weight": content_weight})

# constants_tuning.test_constants("brin", {'title_weight': 0.1, "summary_weight": 0.7, "content_weight": 0.2})