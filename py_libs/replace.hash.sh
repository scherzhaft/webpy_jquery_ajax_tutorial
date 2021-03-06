test "X${USERID}" = "X" && exit 4
test "X${CRYPTHASH}" = "X" && exit 5
test "X${SHA512HASH}" = "X" && exit 6
test "X${MD5HASH}" = "X" && exit 7
EPOCDAY="$(perl -e 'print int(time/(60*60*24))')" ; test "X${EPOCDAY}" = "X" && exit 8
OSNAME="$(/bin/uname -s)"
PASSWD=''  
if [ "${OSNAME}" = Linux ] ; then
  PASSWD="$(echo "${SHA512HASH}"|awk -F'$' {'print $1"\\$"$2"\\$"$3"\\$"$4'})"
elif [ "${OSNAME}" = SunOS ] ; then
  CRYPT_POL="$(grep  "^CRYPT_DEFAULT=" /etc/security/policy.conf|awk -F\= {'print $2'}|awk {'print $1'}|tail -1)"
  test "X${CRYPT_POL}" != "X" && CRYPT_CONF="$(awk {'print $1"="$2'} /etc/security/crypt.conf|grep "^${CRYPT_POL}="|tail -1|awk -F\= {'print $2'})"
  if [[ "${CRYPT_POL}.${CRYPT_CONF}" == *__unix__* ]] ; then
    PASSWD="${CRYPTHASH}"
  elif [[ "${CRYPT_POL}.${CRYPT_CONF}" == *crypt_bsdmd5* ]] ; then
    PASSWD="$(echo "${MD5HASH}"|awk -F'$' {'print $1"\\$"$2"\\$"$3"\\$"$4'})"
  elif [[ "${CRYPT_POL}.${CRYPT_CONF}" == *crypt_sha512* ]] ; then
    PASSWD="$(echo "${SHA512HASH}"|awk -F'$' {'print "\\$"$2"\\$"$3"\\$"$4'})"
  fi
fi
grep "^${USERID}:" /etc/shadow  >/dev/null && {
  test "X${PASSWD}" != "X" && {
    perl -p -i.prev -e "s|^${USERID}:[^:]+:[^:]+|${USERID}:${PASSWD}:${EPOCDAY}|g" /etc/shadow
    case "${OSNAME}" in
      Linux)
        /usr/bin/passwd -u "${USERID}" 1>&2
        /usr/bin/passwd -x 60 "${USERID}" 1>&2
        /sbin/pam_tally2 --user "${USERID}" --reset 1>&2
        exit 0
      ;;
      SunOS)
        /usr/bin/passwd -u "${USERID}" 1>&2
        /usr/bin/passwd -x 60 "${USERID}" 1>&2
        exit 0
    esac
      exit 33
  }  
  exit 35
}
exit 37
