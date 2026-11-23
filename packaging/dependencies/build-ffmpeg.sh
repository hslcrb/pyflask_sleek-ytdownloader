#!/usr/bin/env bash
# Build the separately executed FFmpeg/FFprobe tools and an exact source record.
set -euo pipefail
if [[ $# != 4 ]]; then
  echo "Usage: bash $0 <linux|windows> <source-archive-dir> <work-dir> <binary-dir>" >&2
  exit 2
fi
target="$1"; archives="$(realpath "$2")"; mkdir -p "$3" "$4"
work="$(realpath "$3")"; out="$(realpath "$4")"
jobs="${SLEEK_BUILD_JOBS:-4}"
ff=ffmpeg-8.1.3; lame=lame-3.100
( cd "$archives"; printf "%s\n" "7138d28c96d9d3e3af4ee3d8cad72741f8ffb40da90c1112235dea3ecd3178a3  ffmpeg-8.1.3.tar.xz" "ddfe36cab873794038ae2c1210557ad34857a4b6bdc515785d1da9e175b1da1e  lame_3.100.orig.tar.gz" | sha256sum -c - )
test ! -e "$work/$ff" && test ! -e "$work/$lame"
cd "$work"
tar -xJf "$archives/$ff.tar.xz"
tar -xzf "$archives/lame_3.100.orig.tar.gz"
lame_args=(--disable-shared --enable-static --disable-frontend --disable-decoder --prefix="$work/prefix")
ff_args=(--arch=x86_64 --disable-x86asm --disable-autodetect --disable-gpl
  --disable-nonfree --disable-doc --disable-debug --disable-ffplay --enable-libmp3lame
  --disable-shared --enable-static --enable-small --disable-indevs --disable-outdevs
  --disable-everything
  --enable-protocol=file,http,https,tcp,tls,udp,crypto,pipe,data
  --enable-demuxer=mov,matroska,mp3,aac,ogg,flac,wav,mpegts,hls,concat,srt,webvtt,ass,mpegvideo,image2
  --enable-muxer=mp4,mov,matroska,webm,mp3,adts,ogg,ipod,flac,wav,mpegts,null
  --enable-decoder=aac,aac_latm,mp3,flac,vorbis,opus,pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le,ac3,eac3,alac
  --enable-encoder=libmp3lame,aac,flac,opus,pcm_s16le,pcm_s24le
  --enable-parser=aac,aac_latm,mpegaudio,flac,opus,vorbis,h264,hevc,av1,vp8,vp9
  --enable-bsf=aac_adtstoasc,extract_extradata,h264_mp4toannexb,hevc_mp4toannexb,vp9_superframe,opus_metadata
  --enable-filter=anull,aformat,aresample,volume,format,null)
ext=""
case "$target" in
  linux) ff_args+=(--target-os=linux) ;;
  windows)
    triplet=x86_64-w64-mingw32
    export CC="${MINGW_CC:-x86_64-w64-mingw32-gcc-posix}" AR="$triplet-ar" RANLIB="$triplet-ranlib"
    lame_args+=(--host="$triplet")
    ff_args+=(--target-os=mingw32 --enable-cross-compile --cross-prefix="$triplet-" --cc="$CC"
      --enable-schannel --extra-ldflags=-static)
    ext=.exe ;;
  *) echo "Expected linux or windows." >&2; exit 2 ;;
esac

(cd "$lame"; ./configure "${lame_args[@]}"; make -j"$jobs"; make install)
export PKG_CONFIG_PATH="$work/prefix/lib/pkgconfig"
(cd "$ff";
  ./configure "${ff_args[@]}" --extra-cflags="-I$work/prefix/include" --extra-libs="-L$work/prefix/lib";
  make -j"$jobs" "ffmpeg$ext" "ffprobe$ext"
  cp "ffmpeg$ext" "ffprobe$ext" "$out"
)
cp "$ff/COPYING.LGPLv2.1" "$out/FFmpeg-LGPL-2.1.txt"
cp "$lame/COPYING" "$out/LAME-LICENSE.txt"
printf '%s\n' "Sources: $ff.tar.xz and lame_3.100.orig.tar.gz. No patches." "Build recipe: packaging/dependencies/build-ffmpeg.sh" > "$out/BUILD.txt"
