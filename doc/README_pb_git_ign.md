# Problèmes pour pousser sur le serveur GIT de l'IGN


## Informations

### Système

- OS:
```bash
$ uname -a
Linux RKS1311W030-LINUXUBUNTU 3.13.0-70-generic #113-Ubuntu SMP Mon Nov 16 18:34:13 UTC 2015 x86_64 x86_64 x86_64 GNU/Linux
```

### GIT

- Version de GIT
```bash
$ git --version
git version 1.9.1
```

- Remotes associés au dépot (de travail)
```bash
$ git remote --v
origin	http://gitlab.dockerforge.ign.fr/latty/trafipollu.git (fetch)
origin	http://gitlab.dockerforge.ign.fr/latty/trafipollu.git (push)
origin_github	https://github.com/yoyonel/TrafiPollu.git (fetch)
origin_github	https://github.com/yoyonel/TrafiPollu.git (push)
```

  + Note: J'utilise le portail `http` pour accéder au gitlab de l'IGN

## Problème: échec (retour erreur serveur GIT) pour pousser un/des commits
### Symptomes

- Push de la branche locale (de dev.) vers le remote de l'IGN:
```bash
$ git push origin version_IGN --verbose
Pushing to http://gitlab.dockerforge.ign.fr/latty/trafipollu.git
Counting objects: 90, done.
Delta compression using up to 8 threads.
Compressing objects: 100% (59/59), done.
Writing objects: 100% (66/66), 3.26 MiB | 0 bytes/s, done.
Total 66 (delta 27), reused 0 (delta 0)
POST git-receive-pack (3416460 bytes)
error: RPC failed; result=22, HTTP code = 413
fatal: The remote end hung up unexpectedly
fatal: The remote end hung up unexpectedly
Everything up-to-date
```

- Affichage des tailles (max) des commits (que je tente de push):
```bash
$ git ls-tree -r -t -l --full-name HEAD | sort -n -k 4 | tail
100644 blob bae72731321ad33722f70d7887da4c5033d4559a   89646	doc/README_TrafiPollu_Installation_VM.pdf
100644 blob 0322f6325ad9f9ca9b63c79a4fdaa2e0de547538   94169	gui_doc/Simplified_User_Guide_fichiers/multi_user_tracking_edited_LQ.png
100644 blob 5aae5c17f6199e59856966e3fc42b8aab0a1557c  209546	gui_doc/Simplified_User_Guide_fichiers/auto_save_combined.png
100644 blob c42949bbef9d2c409ef7109a47081b8385b9290b  278621	PyXB_on_Symuvia/reseau.xsd
100644 blob 9500d90a4cb050a015a2f1ec467ea8f801e804d6  281360	gui_doc/Simplified_User_Guide_fichiers/edition_time_with_hexagonal_grid_LQ.png
100644 blob ffd7d268400dd311d3b7598ea1147f201a7b68bb  406998	PyXB_on_Symuvia/reseau_2.04.xsd
100644 blob 43c4f1f20e968af9178430c9c0aec504aca84905  407232	reseau_2.04.xsd
100644 blob 3d4d04325db534228d69648d5222e932042742bb 1182390	PyXB_on_Symuvia_reseau.py
100644 blob fd45e9211dd86aee9071970d13f676906d4c3ed6 3577269	help/utils/plantuml.jar
```

=> A priori, les "gros fichiers" (ou `fat blob`) sont de l'ordre de < ~4mo (le .jar par exemple).

### Google (rapide) sur l'erreur: `error: RPC failed; result=22, HTTP code = 413`
- [error: RPC failed; result=22, HTTP code = 413 fatal: The remote end hung up unexpectedly](https://gitlab.com/gitlab-org/gitlab-ce/issues/1902)
- [Github Push Error: RPC failed; result=22, HTTP code = 413](http://stackoverflow.com/questions/7489813/github-push-error-rpc-failed-result-22-http-code-413)
- [How to solve Git error HTTP 413](http://nknu.net/how-to-solve-git-error-http-413/)
- [git–push large commits over http fail](http://mahingupta.com/gitpush-large-commits-over-http-fail/)

=> Globalement ça parle de modifier le (web) serveur (nginx, Apache, ...) pour accepter des commits plus large.


# Réponse de: Mickael Borne
- mail: [Mickael.Borne@ign.fr](Mickael.Borne@ign.fr)

```
Bonjour,

GIT(LAB) n'est pas fait pour stocker des gros fichiers binaires. La version en place à des problèmes de timeout sur le protocole HTTP d'où ton message d'erreur. On a eu le même problème avec un dépot contenant plein de version d'un JAR.

=> Je t'inviterais bien à te reposer par exemple sur le NEXUS du COGIT pour les JAR.

En mode dépannage, tu peux toujours utiliser le protocole SSH (il n'y a pas ces problèmes de timeout) mais bon...```
```
