#!/usr/bin/python
# vim: set fileencoding=utf8 :
# AUTHOR: Boris Kocherov <bk@raskon.ru>
# LICENSE: http://www.gnu.org/licenses/gpl.html GPLv3
import os
import ldap
import mailbox
import xmpp
from time import localtime, strftime, sleep
CONFIG_FILE = "/etc/dovecot2xmpp_notify_config.py"
XMPP_SERVER = None
FILTER_FUNC = None

if os.path.isfile(CONFIG_FILE):
    execfile(CONFIG_FILE)


MSG_COUNT = {}
FILES_PARSE_CACHE = {}


def maildir_scan(folder):
    cache_false, cache_true = FILES_PARSE_CACHE.setdefault(
        folder,
        (set(), set()),
        )
    md = None
    files = set()
    changed_while_scan = False
    cur_dir = os.path.join(folder, 'cur')
    if os.path.isdir(cur_dir):
        files.update(os.listdir(cur_dir))
    new_dir = os.path.join(folder, 'new')
    if os.path.isdir(new_dir):
        files.update(os.listdir(new_dir))
    for key in cache_true.copy():
        if key not in files:
            cache_true.remove(key)
    for key in cache_false.copy():
        if key not in files:
            cache_false.remove(key)
    for file_name in files:
        if len(cache_true) > MAX_MESSAGE_PARSE:
            break
        if ':2,' in file_name:
            key, flags = file_name.split(':2,')
        else:
            key, flags = file_name, ''
        if 'S' in flags:
            continue
        if (key not in cache_true) and (key not in cache_false):
            if FILTER_FUNC is not None:
                if md is None:
                    md = mailbox.Maildir(folder, factory=None, create=False)
                try:
                    msg = md[key]
                except IOError:
                    changed_while_scan = True
                    break
                except OSError:
                    changed_while_scan = True
                    break
                if FILTER_FUNC(msg):
                    cache_true.add(file_name)
                else:
                    cache_false.add(file_name)
            else:
                cache_true.add(file_name)

    if md:
        md.close()
    if changed_while_scan:
        return None
    else:
        return len(cache_true)


def email_scan(email):
    dirname = base_dir % email
    if os.path.isdir(dirname):
        return maildir_scan(dirname)
    else:
        return 0


def get_users_from_ldap():
    l = ldap.initialize(LDAP_URL)
    l.set_option(ldap.OPT_REFERRALS, 0)
    l.protocol_version = 3
    l.simple_bind_s(LDAP_DN, LDAP_PW)
    users = {}
    mailboxs = {}
    try:
        for dn, entry in l.search_s(LDAP_BIND,
                                    ldap.SCOPE_SUBTREE, LDAP_FILTER,
                                    ['userPrincipalName', 'cn', LDAP_MAIL_ATTR]
                                    ):
            if dn:
                data = {}
                username = entry['userPrincipalName'][0].lower()
                data['username'] = username
                attr_mailboxs = entry.get(LDAP_MAIL_ATTR)
                data['mail'] = attr_mailboxs and attr_mailboxs[0] or ""
                users[username] = data
                for box in attr_mailboxs:
                    mailboxs.setdefault(box, []).append(username)
            else:
                break

    except ldap.OPERATIONS_ERROR:
        pass
    l.unbind_s()
    return mailboxs

jid = xmpp.protocol.JID(XMPP_JID)
if not XMPP_SERVER:
    XMPP_SERVER = jid.getDomain()


def send_xmpp(notices):
    cl = xmpp.Client(XMPP_SERVER, debug=[])
    cl.connect()
    cl.auth(jid.getNode(), XMPP_PASSWORD)
    cl.sendInitPresence()
    for username, n in notices.iteritems():
        for text in n:
            #print strftime("%d %b %Y %H:%M:%S", localtime()), username, text
            cl.send(xmpp.protocol.Message(username, text))
    cl.disconnect()
    del cl

#print get_users_from_ldap()
#send_xmpp({"admin@%s"%XMPP_SERVER:["test",]})
#exit()
if __name__ == "__main__":
    first_run = True
    while 1:
        notifications = {}
        for email, usernames in get_users_from_ldap().iteritems():
            count = email_scan(email)
            if count is None:
                continue
            old_count = MSG_COUNT.setdefault(email, 0)
            if old_count != count:
                if (not first_run) and count > 0 and count > old_count:
                    if count > MAX_MESSAGE_PARSE:
                        text = MESSAGE_MORE % (MAX_MESSAGE_PARSE, email)
                    else:
                        text = MESSAGE % (count, email)
                    for username in usernames:
                        notifications.setdefault(username, []).append(text)
                MSG_COUNT[email] = count
        if notifications:
            send_xmpp(notifications)
        #print 'tic'
        sleep(TIMEOUT)
        first_run = False
