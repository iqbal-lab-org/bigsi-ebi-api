import logging

from flask_restful import Resource
from flask_restful import fields, marshal_with, marshal
from flask_restful import reqparse

from bigsi_aggregator import constants
from bigsi_aggregator.helpers import BigsiAggregator
from bigsi_aggregator.models import SequenceSearch
from bigsi_aggregator.settings import BIGSI_URLS

logger = logging.getLogger(__name__)

parser = reqparse.RequestParser()
parser.add_argument("seq", type=str, help="The sequence query")
parser.add_argument(
    "threshold", type=int, help="The percent k-mer presence result", default=100
)
parser.add_argument("score", type=bool, help="Score the search results", default=False)


bigsi_aggregator = BigsiAggregator(BIGSI_URLS)

search_results_fields = {
    "sample_name": fields.String,
    "percent_kmers_found": fields.Integer,
    "num_kmers_found": fields.String,
    "num_kmers": fields.String,
    "score": fields.Float,
    "mismatches": fields.Float,
    "nident": fields.Float,
    "pident": fields.Float,
    "length": fields.Float,
    "evalue": fields.Float,
    "pvalue": fields.Float,
    "log_evalue": fields.Float,
    "log_pvalue": fields.Float,
    "kmer-presence": fields.String,
    # "metadata": fields.String,  ## In future, metadata associated with 'sampled_name' will be returned
}

search_fields = {
    "id": fields.String,
    constants.SEQUENCE_QUERY_KEY: fields.String,
    constants.THRESHOLD_KEY: fields.Integer,
    constants.SCORE_KEY: fields.Boolean,
    constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.RESULTS_KEY: fields.Nested(search_results_fields),
    "status": fields.String,
    "citation": fields.String,
}


class SequenceSearchListResource(Resource):
    def post(self):
        args = parser.parse_args()

        logger.info(self.post.__name__)
        logger.debug('args: %s', args)

        sequence_search = SequenceSearch.create(
            **args, total_bigsi_queries=len(BIGSI_URLS)
        )
        ## results are stored in the sequence search object
        bigsi_aggregator.search_and_aggregate(sequence_search)
        return marshal(sequence_search, search_fields), 201


class SequenceSearchResource(Resource):
    @marshal_with(search_fields)
    def get(self, sequence_search_id):
        logger.info(self.get.__name__)
        logger.debug('sequence_search_id: %s', sequence_search_id)

        return SequenceSearch.get_by_id(sequence_search_id)
