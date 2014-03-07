

test "X${USERID}" = "X" && exit 4
tty



grep "^${USERID}:" /etc/shadow  >/dev/null && {
  test "X${PASSWD}" != "X" && {
    PASSWD="$(echo "${PASSWD}"|awk -F'$' {'print $1"\\$"$2"\\$"$3"\\$"$4'})"
    perl -p -i.prev -e "s|^${USERID}:[^:]+|${USERID}:${PASSWD}|g" /etc/shadow
    OSNAME="$(/bin/uname -s)"
  
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


