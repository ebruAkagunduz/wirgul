#! -*- coding: utf-8 -*-

import ldap
import ldap.modlist as modlist
from django.conf import settings

class LdapHandler:

    def __init__(self):
        self.servername = "".join(["ldap://",settings.LDAP_SERVER])  # 127.0.0.1
        self.admin_dn = settings.LDAP_ADMIN_DN  # dn
        self.admin_passwd = settings.LDAP_PASSWORD  # passwd

    def connect(self):
        try:
            self.server = ldap.initialize(self.servername)  # ldap.open()
            self.server.protocol_version = ldap.VERSION3
            return True
        except Exception, ex:
            return False

    def bind(self):
        try:
            self.server.bind_s(self.admin_dn, self.admin_passwd)
            return True
        except Exception, ex:
            return False

    def unbind(self):
        self.server.unbind_s()

    def add(self,name,middle_name,surname,email,passwd,guest=False):
        attrs = {}
        if not guest:
            if email.find(settings.EDUROAM_EXCEPTION_DOMAIN) != -1:
                    mail_adr = email.split("@")
                    email_prefix = mail_adr[0]
                    dn= "".join(["mail=",email_prefix,"@",settings.EDUROAM_DOMAIN,",ou=personel,ou=people,dc=comu,dc=edu,dc=tr"])
                    attrs['mail'] = "".join([email_prefix,"".join(["@", settings.EDUROAM_DOMAIN])])
            else:
                mail_adr = email.split("@")
                email_prefix = mail_adr[0]
                if email.find(settings.STUDENT_DOMAIN) != -1:
                    dn="".join(["mail=",email_prefix,"".join(["@", settings.STUDENT_DOMAIN]),",ou=ogrenci,ou=people,dc=comu,dc=edu,dc=tr"])
                    attrs['mail'] = "".join([email_prefix,"".join(["@", settings.STUDENT_DOMAIN])])
                else:
                    dn="".join(["mail=",email_prefix,"".join(["@", settings.EDUROAM_DOMAIN]),",ou=personel,ou=people,dc=comu,dc=edu,dc=tr"])
                    attrs['mail'] = "".join([email_prefix,"".join(["@", settings.EDUROAM_DOMAIN])])
        else:
            prefix = email.split("@")[0]
            email = "@".join([prefix,"comu.edu.tr"])
            dn = "".join(["mail=",email,",ou=personel,ou=people,dc=comu,dc=edu,dc=tr"])
            attrs['mail'] = email
        if settings.USE_CENTRAL_SERVER:
            attrs['objectclass'] = ['organizationalPerson','radiusprofile','person','inetOrgPerson']
        else:
            attrs['objectclass'] = ['organizationalPerson','person','inetOrgPerson']
        if middle_name:
            attrs['givenName'] = " ".join([name,middle_name])
            attrs['cn'] = " ".join([name,middle_name,surname])
        else:
            attrs['givenName'] = name
            attrs['cn'] = " ".join([name,surname])

        attrs['sn'] = surname
        attrs['userPassword'] = passwd
        try :
            ldif = modlist.addModlist(attrs)
            self.server.add_s(dn,ldif)
            return True
        except Exception, ex:
            return False

    def del_user(self, mail, member_type="personel"):
         s = ""
         if member_type == "":
             s = "".join(["mail=",mail,",","ou=people,dc=comu,dc=edu,dc=tr"])
         if member_type == "personel" or member_type == "ogrenci":
             s = "".join(["mail=",mail,",","ou=",member_type,",","ou=people,dc=comu,dc=edu,dc=tr"])
         #print s
         try:
            self.server.delete_s(s)
            return True
         except:
             return False

    def search(self, email, test=False): # sadece mail adresine gore ldapta arama yapmak icin
        base_dn = "ou=people,dc=comu,dc=edu,dc=tr"
        if email.find(settings.EDUROAM_EXCEPTION_DOMAIN) != -1:
            mail_username = email.split("@")[0]
            email = "".join([mail_username,"".join(["@", settings.EDUROAM_DOMAIN])])
        filter = "".join(['mail=',email])
        self.results = self.server.search_s(base_dn, ldap.SCOPE_SUBTREE, filter) # tek elemanli bir list
        if not test:
            return len(self.results)
        else:
            return self.results

    def get_cn(self,email): # sadece mail adresine gore kisinin adini soyadini getirir
        base_dn = "ou=people,dc=comu,dc=edu,dc=tr"
        if email.find("".join(["@", settings.EDUROAM_EXCEPTION_DOMAIN])) != -1:
            mail_adr = email.split("@")
            email = mail_adr[0]
            email = "".join([email,"".join(["@", settings.EDUROAM_DOMAIN])])
        filter = "".join(['mail=',email])
        attr = ['cn']
        results = self.server.search_s(base_dn,ldap.SCOPE_SUBTREE,filter,attr) # tek elemanli bir list
        result_li = list(results)[0] # geri dönen değeri list haline getirdik, tek elemanli listenin elemanını aldık
        cn = result_li[1]['cn'][0]
        return cn.decode("utf-8")

    def modify(self,password,email):
        personel_email = ""
        self.mod_atr = [( ldap.MOD_REPLACE, 'userPassword', password )]
        if email.find("".join(["@", settings.EDUROAM_EXCEPTION_DOMAIN])) != -1:
            mail_adr = email.split("@")
            email_prefix = mail_adr[0]
            personel_email = "".join([email_prefix,"".join(["@", settings.EDUROAM_DOMAIN])])
            use_email = personel_email
            try:
                self.server.modify_s("".join(['mail=',use_email,',ou=personel,ou=people,dc=comu,dc=edu,dc=tr']),self.mod_atr)
                return True
            except Exception, ex:
                return False
        else:
            if email.find(settings.STUDENT_DOMAIN) != -1:
                use_email = email
                try:
                    self.server.modify_s("".join(['mail=',use_email,',ou=ogrenci,ou=people,dc=comu,dc=edu,dc=tr']),self.mod_atr)
                    return True
                except Exception, ex:
                    return False
            else:
                use_email = email
                try:
                    self.server.modify_s("".join(['mail=',use_email,',ou=personel,ou=people,dc=comu,dc=edu,dc=tr']),self.mod_atr)
                    return True
                except:
                    return False

    def modify_student(self,password,email):
        stu_email = ""
        self.mod_atr = [( ldap.MOD_REPLACE, 'userPassword', password )]
        if email.find("".join(["@", settings.EDUROAM_EXCEPTION_DOMAIN])) != -1:
            mail_adr = email.split("@")
            email_prefix = mail_adr[0]
            stu_email = "".join([email_prefix,"".join(["@", settings.STUDENT_DOMAIN])])
        try:
            self.server.modify_s("".join(['mail=',stu_email,',ou=ogrenci,ou=people,dc=comu,dc=edu,dc=tr']),self.mod_atr)
            return True
        except:
            return False


if __name__ == "__main__":
    op = LdapHandler()
    op.connect()
    op.bind()
    #op.add("test.ldif")
    #print op.modify_ogrenci("080401018@comu.edu.tr", "M1Quw", "engine123")
    #op.modify_personel("100000001@comu.edu.tr", "be9U7C3Q", "16e9U7C3Q")     op.modify_ogrenci("100000001@comu.edu.tr", "be9U7C3Q", "16e9U7C3Q")
    #print op.search("user1@comu.edu.tr", member_type="ogrenci")
    op.del_user("oguzyarimtepe@comu.edu.tr")
    op.unbind()



