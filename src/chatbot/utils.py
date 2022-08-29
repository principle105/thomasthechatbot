import nltk


def download_nltk_data(quiet=False):
    downloads = (
        "stopwords",
        "punkt",
        "wordnet",
        "averaged_perceptron_tagger",
        "omw-1.4",
    )

    for d in downloads:
        nltk.download(d, quiet=quiet)
