# Part of osadmin. See LICENSE file for full copyright and licensing details.
# License: OPL-1 (https://www.odoo.com/documentation/18.0/legal/licenses.html#odoo-apps)

# The key is the text in hexadecimal: the database sorts it the same way under
# every collation. A database restored under nl_BE.UTF-8 ignores the hyphens
# when it sorts plain text, so 3L037-120 would end up between the sizes of
# 3L037-12. Hexadecimal digits sort alike under every collation.
#
# SEPARATOR is lower than the hexadecimal code of any printable character, so
# "3L037-12" + SEPARATOR + size comes before "3L037-120".
SEPARATOR = '01'
# After every reference: a product without one comes last.
NO_REFERENCE = 'g'


def to_hex(text):
    return (text or '').encode().hex()
