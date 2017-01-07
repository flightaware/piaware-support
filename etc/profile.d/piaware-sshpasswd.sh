# modelled after the Raspbian variant
# if ssh is enabled, test for the default piaware password and
# complain if it matches

check_hash ()
{
   test -x /usr/bin/mkpasswd || return 0
   if [ $(id -un) != "pi" ]; then return 0; fi
   if grep -q "^PasswordAuthentication\s*no" /etc/ssh/sshd_config ;then return 0 ; fi

   HASH=$(sudo -n getent shadow pi 2>/dev/null | cut -f2 -d:)
   SALT=$(echo "$HASH" | cut -f3 -d\$)
   test -n "$SALT" || return 0

   DEFHASH=$(mkpasswd -msha-512 flightaware "$SALT" 2>/dev/null)
   if [ "$HASH" = "$DEFHASH" ]
   then
       echo >&2
       echo "SSH is enabled and the default password for the 'pi' user has not been changed." >&2
       echo "This is a security risk - please type 'passwd' to set a new password." >&2
       echo >&2
   fi
}

if /usr/sbin/service ssh status 2>/dev/null | grep -q running; then
    check_hash
fi

unset check_hash
