# vim: set fileencoding=utf8 :
base_dir = "/var/virtual/%s/"
local_domain = "testtest.org"
LDAP_URL = "ldap://192.168.1.1/"
LDAP_DN = r"DOMAIN\user"
LDAP_PW = "supertest"
LDAP_BIND = "dc=testtest,dc=org"
LDAP_MAIL_ATTR = "postOfficeBox"
LDAP_FILTER = "(&(objectClass=user)(%s=*))" % LDAP_MAIL_ATTR

XMPP_JID = '_dovecot@testtest.org'
XMPP_PASSWORD = 'supertest'
XMPP_SERVER = "192.168.1.1"

MAX_MESSAGE_PARSE = 10
TIMEOUT = 60

MESSAGE = "you have %d not seen messages in %s mailbox"
MESSAGE_MORE = "you have more %d not seen messages in %s mailbox"
#MESSAGE = "у вас %d непрочитанных сообщений в ящике %s"
#MESSAGE_MORE = "у вас больше %d непрочитанных сообщений в ящике %s"

from email.utils import getaddresses
def FILTER_FUNC(msg):
    msg_from = getaddresses(msg.get_all('from', []))
    if msg_from:
        msg_from = msg_from[0][1]
        domain = msg_from.split('@')
        if len(domain) == 1:
            domain = local_domain
        else:
            domain = domain[-1].lower()
    #return domain.endswith(local_domain)
    return domain == local_domain
    
