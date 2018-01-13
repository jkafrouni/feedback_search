# Feedback Search (COMS 6111 - Fall 17 - Project 1)

Implementation of an information retrieval system that exploits user-provided relevance feedback to improve the search results returned by Google.

This is a project that I developped in Fall 2017 for the course COMS 6111 Advanced Database Systems taught by Professor Luis Gravano at Columbia University.
Below are the instructions and the readme that I submitted for the project.

## Submitted files

* README.md
* config.py
* feedback_search
    * __init__.py
    * __main__.py
    * constants.py
    * enhance_query.py
    * feedback.py
    * index.py
    * preprocess.py
    * query.py
    * scrape.py
* logs
    * feedback_search.log
* queries_transcript.txt
* requirements.txt
* resources
    * stopwords.txt
* run_tests.py
* setup.py
* tests
    * constants_tuning.py
    * mock_feedback.py
    * mock_query_and_scraping.py
    * parameters_tuning.txt
    * query_history.json

## How to install & run

From the top_level *feedback_search* folder, install all the requirements with:
```
bash setup.sh
```
Then run the project with:
```
python3 -m feedback_search <query> <desired precision>
```
For example:
```
python3 -m feedback_search "information research" 0.9
```

You will need credentials for the Google API that you need to place in a file called config.py which should contain two variables,
DEVELOPER_KEY and SEARCH_ENGINE_ID.

## Internal design

### Project flow

The user enters a query along with the desired precision. The Google API returns the best 10 results and the user provides his feedback for each of the documents. While he is doing that, 10 threads are scraping the corresponding URLs in order to get the content of the pages that will be used along with the title and summary. Then the precision is calculated based on the user's feedback, we stop either if precision is 0 or if precision is better than the precision requested by the user, otherwise we compute an augmented query, query the Google API again, and get the user's feedback, until desired precision is obtained.

The main loop controlling this flow is in the *main()* method in *__main__.py*. Each part of the project is in a separate class, which allows better abstraction. In particular, this abstraction lets us build different indexes for different purposes (one for each 'zone' of a document, for both single terms (unigrams) and bigrams, see part e)). Such an abstraction would also let us, with little effort, change the query API, change the weights in the query expansion algorithm or the whole algorithm, change the modules used for preprocessing, etc. 

### Main functions
The different functions performed are:
* main: the main loop, by __main__.py
* get content of url: by scrape.py
* query the Google API: by query.py
* ask user's feedback: by feedback.py
* preprocess the sentences (tokenization, stemming, bi-gram generation...): by preprocess.py
* build index and inverted file: by index.py
* enhance the query: by enhance_query.py

### Preprocessing
For the preprocessing, we first tokenize the sentences (remove punctuation, put in lower case, remove stopwords), and then potentially apply the PorterStemmer from NLTK library (see note [1]).
If the query contains stopwords, then we don't remove these stopwords from documents.

We also generate bi-grams from the sentences in order to build a bi-gram index that will be used to give importance to the order of words when words are added to the query. (see section e)

The preprocessing is called by each index himself, from its preprocess method which used functions from preprocess.py. 

### Index
As said above, we build an index for each zone of the document: title, summary, and content. If the scraping fails, the 'content' field of the document is empty and all the associated weights are 0. We do this with single terms (unigrams) as well as bigrams, therefore we have a total of 6 indexes that are built in parallel (with python threads). This approach lets us easily take into account the position of the words in one of these three zones in our weightning. 

To implement this, I had the choice betweenn using pythons dicts which offer quick access but consume memory or numpy matrices. I chose numpy matrices because: 1) we can do matrix computations instead of loops over dimensions, which is faster (numpy operations are done in C) and makes the code cleaner, 2) we can easily combine the weights by simple linear combinations of vectors, yet one can argue that in this context it would be a better choice to use dicts as there are only a few documents and their sizes are small, which means dicts would not consume too much memory anyway. Another drawback is that using large numpy matrices (quite sparse) instead of dicts makes the project a little slower. Yet, this implementation is ready for scaling and could be used for a query engine that provides much more data, and, again, the code is more clear.

The index class objects have methods to compute term frequency and inverse document frequency, which allows to test easily different variants of weighting. The three main components of Index object class are:
* **self.docs_tf_vectors** : list of length 10, each element corresponds to a document and is a list that contains in position i the term frequency in that document of the term indexed i in our global vocabulary. This is not a numpy array because we don't need to perform matrix operations on these, but only access them in self.log_tf. Lists are used instead of dicts because they're smaller in memory. \[\[ tf(word_0, doc_0), tf(word_1, doc_0) ... ], ...]
* **self.vocabulary_index** : a dict containing the index (in the global vocabulary) of each word: {'word': index}
* **self.inverted_file** : list of length the number of words in the vocabulary, each element in position iis the set of document ids for documents that contain the word number i.

### Tests
The project also contains some test files. Each time the project is run, the results of the query and the scraping are stored in a json to allow to run a series of tests without querying the search engine / scraping. See *mock_query_and_scraping.py* functions. We are then able to run tests for different constants values from the *run_tests.py* file at the root, which calls test functions in the *tests/* folder. Some results of the tests are available in *tests/parameters_tuning.txt* as an example.

## Query modification method used

#### Rocchio's algorithm:

The main algorithm used is the Rocchio algorithm, yet in a modified version. For each zone of the documents ('title', 'summary', 'content'), we perform the classic algorithm. The constants alpha, beta, gamma of Rocchio algorithm choosed are the "reasonable settings" that we can find in the litterature: alpha = 1, beta = 0.75, gamma = 0.15 *(Manning, Raghavan, and Schütze Introduction to Information Retrieval, Chapter 9)*, ie we give much more value to the relevant documents than the non relevant ones. All the constants of the project are set in the constants.py file. 

#### Combining zones:
The weights obtained from each zone are then linearly combined to obtain "global" weights, using coefficients title_weight, summary_weight, content_weight that are again in constants.py. Unlike Rocchio's constants that have been taken from the litterature, these coefficient have been tuned using the tests from constants_tuning.py. The setting of these constants doesn't entirely rely on these tests as: 1) only a few tests we run, 2) we need to avoid over fitting on these tests. Therefore, the constants have also been set by following these observations:
* 'Title' fields are short, and most of the time contain the name of the website, therefore if the title_weight is too high the augmented query will probably contain "Wikipedia" or "IMDB" for example, as these websites are likely to appear several times in the top-10 results. One solution to avoid this would be to collect a dataset of the most popular websites and add them to the stopwords.
* 'Summary' fields are of medium size, clean, and contain quite relevant information. The associated weight should be high.
* 'Content' fields can be noisy / dirty, yet do have value so the coefficient shouldn't be high but it's still usefull to set it non zero.

#### Order of words:

To take into account the order of words, we perform exactly the same as above (one index per zone, combine the zones), on an index of bi-grams (unigram and bigram indexers are implemented the same way, see the parent Indexer class for both classes, only the preprocessing part differs for each of the children).

We compute weights of bigrams by linearly combining the two following bi-gram weights:
* Weights that are computed using "pseudo-Rocchio", by combining the centroids of relevant and non relevant document, with the same beta and gamma as before
* Weights that are computed by taking the average weight between term 1 and term 2 in the (term 1, term 2) bigram

During the tests, I noticed that these two weights are actually close and the way they are linearly combined doesn't affect too much the result. To gain some speed, we could remove the first type of bigram weights, yet the "Rocchio style" computations are not the bottleneck in this implementation, the index construction is. 

At this point, we have weights for unigrams (computed using Rocchio's Algorithm on different zones), and weights on bi-grams (computed as described above), the final step is to take the best bi-grams, which is done in *RocchioQueryOptimizer.choose_best_bigram*: 
* if the query contains one word of a highly weighted bigram: we add the second term in the bigram, in the right order, and then complete the query with a third unigram that is best weighted an not one of these terms
* if the query doesn't contain a word of a highly weighted bigram (less likely to happen, at least not at first iteration), we add the best-weighted bigram.

## Disclosures

In this project, we use an implementation of the PorterStemmer algorithm from the NLTK python module.

## Notes

[1] In the tests, it appears that the PorterStemmer effect on the quality of the augmented queries isn't significant, and can sometimes decrease the quality results (e.g. plural queries like "Bulls"). We could choose to tweak the PorterStemmer (for the previous example, do not stem words that are in query), **I chose to disable the stemming (see constants.py)**. If the stemming was enabled, it could lead to augmented queries where the words from the original query have been stemmed and therefore are likely to have been modified, which does not respect one of the rules of the project assignment. To avoid this, we would need to modify the code to take this into account, which wasn't worth it
