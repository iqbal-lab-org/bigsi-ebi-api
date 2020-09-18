import logging

from bigsi_aggregator.tasks import search_bigsi_and_update_results


logger = logging.getLogger(__name__)


class BigsiAggregator:
    def __init__(self, bigsi_urls):
        logger.info(self.__init__.__name__)
        logger.debug('bigsi_urls: %s', bigsi_urls)

        self.bigsi_urls = bigsi_urls

    def search_and_aggregate(self, sequence_search):
        logger.info(self.search_and_aggregate.__name__)
        logger.info('sequence_search: %s', sequence_search)

        for url in self.bigsi_urls:
            result = search_bigsi_and_update_results.delay(url, sequence_search.id)
