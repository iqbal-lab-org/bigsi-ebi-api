import logging

import requests

from bigsi_aggregator.extensions import celery
from bigsi_aggregator.models import SequenceSearch
from bigsi_aggregator.models import VariantSearch

logger = logging.getLogger(__name__)


class BigsiClient:
    def __init__(self, url):
        self.base_url = url

    def search(self, seq, threshold, score):
        logger.info(self.search.__name__)
        logger.debug('seq: %s', seq)
        logger.debug('threshold: %s', threshold)
        logger.debug('score: %s', score)

        url = "{base_url}/search".format(base_url=self.base_url)
        results = requests.post(
            url,
            data={"seq": seq, "threshold": int(threshold) / 100, "score": int(score)},
        ).json()
        return results

    def variant_search(self, vs):
        url = "{base_url}/variant_search".format(base_url=self.base_url)
        response = requests.post(
            url,
            data={
                "reference": vs.reference,
                "ref": vs.ref,
                "pos": vs.pos,
                "alt": vs.alt,
                "genbank": vs.genbank,
                "gene": vs.gene,
            },
        )
        return response.json()


@celery.task(name="search_bigsi_and_update_results")
def search_bigsi_and_update_results(url, sequence_search_id):
    logger.info(search_bigsi_and_update_results.__name__)
    logger.debug('sequence_search_id: %s', sequence_search_id)

    sequence_search = SequenceSearch.get_by_id(sequence_search_id)
    bigsi_client = BigsiClient(url)
    bigsi_search_results = bigsi_client.search(
        sequence_search.seq, sequence_search.threshold, sequence_search.score
    )
    sequence_search.add_results(bigsi_search_results["results"])


@celery.task(name="variant_search_bigsi_and_update_results")
def variant_search_bigsi_and_update_results(url, variant_search_id):
    variant_search = VariantSearch.get_by_id(variant_search_id)
    bigsi_client = BigsiClient(url)
    bigsi_search_results = bigsi_client.variant_search(variant_search)
    variant_search.add_results(bigsi_search_results["results"])
