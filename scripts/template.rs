#![crate_type="cdylib"]#![no_std]#[no_link]extern crate std;#[link_section=".interp"]static I:[u8;28]=*b"/lib64/ld-linux-x86-64.so.2\0";#[link_section=".text"]#[no_mangle]static _start:[u64;%(len)s]=[%(text)s];