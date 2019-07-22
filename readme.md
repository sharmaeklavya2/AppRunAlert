# AppRunAlert

The script `app_run_alert.py` runs a program specified on the command-line.
If that program fails, it sends an email with the failure details.

It uses `curl` to talk to an SMTP server using the SMTPS protocol.
The default SMTP server is the one by Gmail.

If you don't have your own SMTP server, you may want to read this article:
[How to Utilize Google’s Free SMTP Server to Send Emails](https://kinsta.com/knowledgebase/free-smtp-server/)
