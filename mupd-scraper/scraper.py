#!/usr/bin/env python
# coding: utf-8

from bs4 import BeautifulSoup
from datetime import timedelta
import requests
import requests_cache
from time import sleep
import csv
import smtplib


requests_cache.install_cache(
    'cache',
    expire_after=timedelta(hours=24),
    allowable_methods=('GET', 'POST')
)

BLOTTER_URL = 'https://mupolice.missouri.edu/mupd/blotter/'

def get_tables():
    r = requests.get(BLOTTER_URL)
    soup = BeautifulSoup(r.content, 'lxml')

    options = soup.find('select', id = 'sfilter').find_all('option')

    tables = []

    for opt in options:
        value = opt.attrs['value']
        if len(value) > 0:
            tables.append(value)

    return tables

def get_resutls(result):
    r = requests.post(
        BLOTTER_URL,
        data={'sfilter': result}
    )

    r.raise_for_status()

    return r.content


def get_data(search_results, writer, old_cases):
    soup = BeautifulSoup(search_results, 'lxml')

    table = soup.find('table')

    trs = table.find_all('tr')[2:]

    ctr = 0
    numCrimes = 0
    body = 'NEW CRIMES FOUND:\n'
    for tr in trs:
        tds = tr.findAll('td')

        if ctr % 2 == 0:
            case_number = tds[0].text.strip()
            date_time_reported = tds[1].text.strip()
            location_of_occurence = tds[2].text.strip()
            domesticdv_relationship = tds[3].text.strip()
            incident_type = tds[4].text.strip()
            criminal_offense = tds[5].text.strip()
            disposition = tds[6].text.strip()
        else:
            date_time_occured = tds[0].text.strip()
            record = [
                case_number, date_time_reported,
                date_time_occured, location_of_occurence,
                domesticdv_relationship, incident_type, criminal_offense, disposition
                ]
            writer.writerow(record)
            #print(record)
            if case_number not in old_cases:
                txt = '\n{}\n- {}\n- {}\n- {}\n- {}\n'.format(case_number, date_time_occured, location_of_occurence,
                criminal_offense, disposition)
                body += txt
                numCrimes += 1
        ctr += 1
    if numCrimes == 0:
        body='No new updates.'

    send_email(body, numCrimes)
    print(body)

def get_case(csv_file):
    reader = csv.reader(
        open(csv_file), delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
    case_nums = set()
    for row in reader:
        case_num = row[0]
        case_nums.add(case_num)
    return case_nums

def send_email(email_body, numRequests):
    for toaddr in ['news@ColumbiaMissourian.com']:
            fromaddr = 'mupdscraper@gmail.com'
            pwd = 'MIZSpring20'
            msg = "\r\n".join([
                    "From: {}".format(fromaddr),
                    "To: {}".format(toaddr),
                    "Subject: {} MUPD new cases".format(numRequests),
                    "",
                    "{}".format(email_body)
                    ])
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(fromaddr, pwd)
            server.sendmail(fromaddr, toaddr, msg)
            server.quit()
    print('\nEmail sent!')

def main():
    table = 36
    old_cases = get_case('report_final.csv')
    with open('report_final.csv', 'w', newline='') as f:
        writer = csv.writer(
            f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL
            )

        writer.writerow(['case_number','date_time_reported','date_time_occured',
        'location_of_occurence','domesticdv_relationship','incident_type',
        'criminal_offense','disposition'
        ])

        search_results =  get_resutls(table)

        get_data(search_results, writer, old_cases)

        sleep(3)

if __name__ == '__main__':
    main()
