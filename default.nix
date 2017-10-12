#!/usr/bin/env nix-shell

with import <nixpkgs> {};

let
  envname = "nglesspy";
  python = python36;
  pyp = python36Packages;
  pys = with pyp; [
    six
    argparse
    urllib3
    chardet
    requests
  ];
in

stdenv.mkDerivation { 
  name = "${envname}-env";
  propagatedBuildInputs = [
     python
     zlib
     pys
    ];
  src = null;
  # When used as `nix-shell --pure`
  shellHook = ''
  '';
  # used when building environments
  extraCmds = ''
  '';
}

