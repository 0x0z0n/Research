set-git-ssh() {
  git config core.sshCommand "ssh -i ~/.ssh/$1 -F /dev/null"
}
