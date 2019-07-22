#!/usr/bin/env python3

"""Run a program. If it fails, send details to an email address."""

from __future__ import print_function

import os
import sys
import subprocess
import argparse
from datetime import datetime


DEFAULT_SMTP_SERVER = 'smtps://smtp.gmail.com:465'

TIMEOUT = 60

MAIL_TEMPLATE = """
From: {from_email}
To: {to_email}
Subject: {subject}

{body}
""".strip()


def send_mail(smtp_server, from_email, to_email, auth_email, auth_passwd, subject, body):

    content = MAIL_TEMPLATE.format(from_email=from_email, to_email=to_email,
        subject=subject, body=body)

    args = ['curl', '--silent', '--show-error',
        '--url', smtp_server,
        '--ssl-reqd',
        '--mail-from', from_email,
        '--mail-rcpt', to_email,
        '--user', '{}:{}'.format(auth_email, auth_passwd),
        '-T', '-']

    procrun = subprocess.run(args, input=content, text=True,
        capture_output=True, timeout=TIMEOUT)
    if procrun.stdout:
        print('curl stdout:', procrun.stdout.strip())
    if procrun.stderr:
        print('curl stderr:', procrun.stderr, file=sys.stderr)
    procrun.check_returncode()


def data_text_summary(data):
    try:
        res = data.decode('UTF-8')
    except UnicodeDecodeError as e:
        res = '{}: {}\n{}'.format(type(e).__name__, str(e), str(data))
    SUMMARY_LIMIT = 2000
    if len(res) > SUMMARY_LIMIT:
        res = res[:SUMMARY_LIMIT - 3] + '...'
    return res


class ProcResult(object):
    def __init__(self, args, start_time, end_time, errcode, errmsg, returncode, stdout, stderr):
        self.args = args
        self.start_time = start_time
        self.end_time = end_time
        self.errcode = errcode
        self.errmsg = errmsg
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return 'ProcResult({})'.format(self.args)

    def get_status(self):
        program_name = os.path.basename(self.args[0])
        base = 'AppRunAlert'
        if self.errcode is not None:
            return '{}: {} failed with error {}'.format(base, program_name, self.errcode)
        else:
            return '{}: {} failed with status {}'.format(base, program_name, self.returncode)

    def get_report(self):
        lines = [
            'COMMAND: {}'.format(self.args),
            'TIME: {} to {} ({})'.format(
                self.start_time, self.end_time, self.end_time - self.start_time),
        ]
        if self.errcode is not None:
            lines.append('ERRCODE: {}'.format(self.errcode))
        if self.errmsg is not None:
            lines.append('ERRMSG: {}'.format(self.errmsg))
        if self.returncode is not None:
            lines.append('RETURNCODE: {}'.format(self.returncode))
        if self.stderr:
            lines.append('\nSTDERR:\n{}'.format(data_text_summary(self.stderr)))
        if self.stdout:
            lines.append('\nSTDOUT:\n{}'.format(data_text_summary(self.stdout)))
        return '\n'.join(lines)


def get_proc_result(args, timeout=None):
    start_time = datetime.now()
    try:
        procrun = subprocess.run(args, capture_output=True, timeout=timeout)
        returncode, stdout, stderr = procrun.returncode, procrun.stdout, procrun.stderr
        errcode, errmsg = None, None
    except FileNotFoundError as e:
        returncode, stdout, stderr = None, None, None
        errcode, errmsg = type(e).__name__, str(e)
    end_time = datetime.now()
    return ProcResult(args=args, start_time=start_time, end_time=end_time,
        errcode=errcode, errmsg=errmsg, returncode=returncode,
        stdout=stdout, stderr=stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-email', required=True)
    parser.add_argument('--to-email', required=True)
    parser.add_argument('--auth-email')
    parser.add_argument('--passwd', required=True)
    parser.add_argument('--timeout', type=float)
    parser.add_argument('--smtp-server', default=DEFAULT_SMTP_SERVER)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.args:
        print('error: no program to run.', file=sys.stderr)
        sys.exit(2)
    if not args.auth_email:
        args.auth_email = args.from_email

    proc_result = get_proc_result(args.args, args.timeout)
    # print(proc_result.get_report())
    if proc_result.errcode or proc_result.returncode != 0:
        send_mail(args.smtp_server, args.from_email, args.to_email, args.auth_email, args.passwd,
            proc_result.get_status(), proc_result.get_report())


if __name__ == '__main__':
    main()
