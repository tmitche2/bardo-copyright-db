import argparse
from datetime import datetime, timedelta

from sessionManager import SessionManager
from builder import CCEReader
from renBuilder import CCRReader
from esIndexer import ESIndexer
from helpers.config import loadConfig


def main(secondsAgo=None, year=None, exclude=None, reinit=False):
    manager = SessionManager()
    manager.generateEngine()
    manager.initializeDatabase(reinit)
    manager.createSession()

    loadFromTime = None
    startTime = datetime.now()
    if secondsAgo is not None:
        loadFromTime = startTime - timedelta(seconds=secondsAgo)

    if exclude != 'cce':
        loadCCE(manager, loadFromTime, year)
    if exclude != 'ccr':
        loadCCR(manager, loadFromTime, year)

    indexUpdates(manager, loadFromTime)

    manager.closeConnection()


def loadCCE(manager, loadFromTime, selectedYear):
    cceReader = CCEReader(manager)
    cceReader.loadYears(selectedYear)
    cceReader.getYearFiles(loadFromTime)
    cceReader.importYearData()


def loadCCR(manager, loadFromTime, selectedYear):
    ccrReader = CCRReader(manager)
    ccrReader.loadYears(selectedYear, loadFromTime)
    ccrReader.importYears()


def indexUpdates(manager, loadFromTime):
    esIndexer = ESIndexer(manager, loadFromTime)
    esIndexer.indexRecords(recType='cce')
    esIndexer.indexRecords(recType='ccr')


def parseArgs():
    parser = argparse.ArgumentParser(
        description='Load CCE XML and CCR TSV into PostgresQL'
    )
    parser.add_argument('-t', '--time', type=int, required=False,
                        help='Time ago in seconds to check for file updates')
    parser.add_argument('-y', '--year', type=str, required=False,
                        help='Specific year to load CCE entries and/or renewals from')
    parser.add_argument('-x', '--exclude', type=str, required=False,
                        choices=['cce', 'ccr'],
                        help='Specify to exclude either entries or renewals from this run')
    parser.add_argument('--REINITIALIZE', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parseArgs()
    try:
        loadConfig()
    except FileNotFoundError:
        pass

    main(
        secondsAgo=args.time,
        year=args.year,
        exclude=args.exclude,
        reinit=args.REINITIALIZE
    )
