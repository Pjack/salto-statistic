#!/usr/bin/python3
'''
program to calculate how many people come to office in a period.
'''
import sys
import logging
import argparse
import csv
import datetime

logger = logging.getLogger(__name__)

LT_FORMAT = '%m/%d/%Y %H:%M:%S'


def parse_options():
    """
    parse options
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('csvfile', help='filename of csv file')
    parser.add_argument('-o', '--output', default='slim', choices=['slim', 'wide', 'csv'], help='output format',
                        type=str)
    parser.add_argument('-s', '--sort', default='user', choices=['user', 'day'], help='sort by user or day',
                        type=str)
    parser.add_argument('-d', '--debug', action='store_true', help='Turn on debug info',
                        default=False)

    options = parser.parse_args()

    if options.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

    logging.debug(options)

    return options


def compute_stats(csvfile):
    '''
    :param csvfile: the filename of csv file
    '''
    checkin_stats = {}
    checkin_stats['employees'] = {}
    checkin_stats['start_date'] = datetime.date(2100, 12, 31)
    checkin_stats['end_date'] = datetime.date(1900, 1, 1)
    checkin_raw = {}

    with open(csvfile, newline='', encoding='utf-8') as f_handle:
        checkin_reader = csv.DictReader(f_handle, delimiter=',')

        for row in checkin_reader:
            if not row.get('User First Name', ''):
                continue

            # Full name
            full_name = row.get('User First Name', '')
            if row.get('User Last Name'):
                full_name = full_name + ' ' + row.get('User Last Name')

            # Find the day
            checkin_time = datetime.datetime.strptime(row['Local Time'], LT_FORMAT)
            checkin_date = checkin_time.date()

            # overall = {
            #   'start_date': date
            #   'end_date': date
            #   'employees': {
            #        'name1': {date1, date2, date3}
            #        'name2': {date1, date2, date3}
            #   }
            if full_name not in checkin_stats['employees']:
                checkin_stats['employees'][full_name] = set([checkin_date])
            else:
                checkin_stats['employees'][full_name].add(checkin_date)

            # Calculate the start time and end time
            if checkin_date < checkin_stats['start_date']:
                checkin_stats['start_date'] = checkin_date
            if checkin_date > checkin_stats['end_date']:
                checkin_stats['end_date'] = checkin_date

            # raw = {
            #   'name1': { 'date': [start_time, end_time] }
            #   'name2': { 'date': [start_time, end_time] }
            # }
            if full_name not in checkin_raw:
                checkin_raw[full_name] = {checkin_date: [checkin_time, checkin_time]}
            elif checkin_date not in checkin_raw[full_name]:
                checkin_raw[full_name][checkin_date] = [checkin_time, checkin_time]
            else:
                if checkin_time < checkin_raw[full_name][checkin_date][0]:
                    checkin_raw[full_name][checkin_date][0] = checkin_time
                if checkin_time > checkin_raw[full_name][checkin_date][1]:
                    checkin_raw[full_name][checkin_date][1] = checkin_time

    logger.debug(checkin_stats['start_date'])
    logger.debug(checkin_stats['end_date'])
    # logger.debug(checkin_stats['employees'])
    # for employee,checkin in checkin_raw.items():
    #    logger.debug(f"{employee} {checkin}")

    return checkin_stats, checkin_raw


def output_stats(package_stats, options):
    '''
    :param package_stats: the statistic data of employees
    '''
    if options.sort == 'user':
        employees = sorted(package_stats['employees'].items(), key=lambda x: x[0])
    else:
        employees = sorted(package_stats['employees'].items(), key=lambda x: len(x[1]))
    for employee in employees:
        checkindays = ""
        s_day = None
        e_day = None
        for day in sorted(employee[1]):
            if not s_day:
                s_day = e_day = day
            elif (day - e_day).days == 1:
                e_day = day
            else:
                if s_day == e_day:
                    checkindays += f"{s_day.strftime('%m/%d')}, "
                else:
                    checkindays += f"{s_day.strftime('%m/%d')}~{e_day.strftime('%m/%d')}, "
                s_day = e_day = day
        else:
            if s_day == e_day:
                checkindays += f"{s_day.strftime('%m/%d')}, "
            else:
                checkindays += f"{s_day.strftime('%m/%d')}~{e_day.strftime('%m/%d')}, "
        if options.output == 'slim':
            print(f"{employee[0]:<25} come {len(employee[1]):>3} days")
        else:
            print(f"{employee[0]:<25} come {len(employee[1]):>3} days   {checkindays.strip(', ')}")
    print(
        f"\nDuring {package_stats['start_date']} ~ {package_stats['end_date']}, "
        f"total employees: {len(package_stats['employees'])}")


def output_csv(raw_data, options):
    employees = sorted(raw_data.items(), key=lambda x: x[0])

    with open('output.csv', 'w', newline='') as csvfile:
        fieldnames = ['name', 'date', 'checkin', 'checkout', 'hours']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for employee in employees:
            days = sorted(employee[1].items(), key=lambda x: x[0])
            for day in days:
                csvdata = {'name': employee[0], 'date': day[0], 'checkin': day[1][0], 'checkout': day[1][1],
                           'hours': (day[1][1] - day[1][0])}
                writer.writerow(csvdata)

        # writer.writerow({'first_name': 'Baked', 'last_name': 'Beans'})
        # writer.writerow({'first_name': 'Lovely', 'last_name': 'Spam'})
        # writer.writerow({'first_name': 'Wonderful', 'last_name': 'Spam'})


def main():
    """
    download file and parse the content
    """
    options = parse_options()
    logger.debug(options)
    print("Computing the statistics...")
    checkin_stats, checkin_raw = compute_stats(options.csvfile)
    if options.output == 'csv':
        output_csv(checkin_raw, options)
    else:
        output_stats(checkin_stats, options)


if __name__ == "__main__":
    sys.exit(main())
