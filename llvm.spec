# Components enabled if supported by target architecture:
%ifarch %ix86 x86_64
  %bcond_without gold
%else
  %bcond_with gold
%endif

%define _prefix /opt/llvm-5.0.0
%define _pkgdocdir %{_docdir}/llvm

Name:		llvm-5.0.0
Version:	5.0.0
Release:	2.svn312333%{?dist}.alonid
Summary:	The Low Level Virtual Machine

License:	NCSA
URL:		http://llvm.org
Source0:	http://llvm.org/releases/%{version}/657c31173ea30090583e40c7a9204561d9c2d8c4.tar.gz

Source100:	llvm-config.h

# recognize s390 as SystemZ when configuring build
Patch0:		llvm-3.7.1-cmake-s390.patch
Patch1:		0001-Hack-on-recursion-limit.patch

BuildRequires:	cmake
BuildRequires:	zlib-devel
BuildRequires:  libffi-devel
BuildRequires:	ncurses-devel
%if 0%{?fedora} >= 24
BuildRequires:	python3-sphinx
%else
BuildRequires:	python
%endif
%if %{with gold}
BuildRequires:  binutils-devel
%endif
BuildRequires:  libstdc++-static

Requires:	%{name}-libs%{?_isa} = %{version}-%{release}

%description
LLVM is a compiler infrastructure designed for compile-time, link-time,
runtime, and idle-time optimization of programs from arbitrary programming
languages. The compiler infrastructure includes mirror sets of programming
tools as well as libraries with equivalent functionality.

%package devel
Summary:	Libraries and header files for LLVM
Requires:	%{name}%{?_isa} = %{version}-%{release}

%description devel
This package contains library and header files needed to develop new native
programs that use the LLVM infrastructure.

%package doc
Summary:	Documentation for LLVM
BuildArch:	noarch
Requires:	%{name} = %{version}-%{release}

%description doc
Documentation for the LLVM compiler infrastructure.

%package libs
Summary:	LLVM shared libraries

%description libs
Shared libraries for the LLVM compiler infrastructure.

%package static
Summary:	LLVM static libraries

%description static
Static libraries for the LLVM compiler infrastructure.

%prep
%setup -q -n llvm-657c31173ea30090583e40c7a9204561d9c2d8c4
%patch0 -p1 -b .s390
%patch1 -p1

%build
mkdir -p _build
cd _build

%ifarch s390
# Decrease debuginfo verbosity to reduce memory consumption during final library linking
%global optflags %(echo %{optflags} | sed 's/-g /-g1 /')
%endif

# force off shared libs as cmake macros turns it on.
%cmake .. \
	-DBUILD_SHARED_LIBS:BOOL=OFF \
	-DCMAKE_BUILD_TYPE=RelWithDebInfo \
	-DCMAKE_SHARED_LINKER_FLAGS="-Wl,-Bsymbolic -static-libstdc++" \
%ifarch s390
	-DCMAKE_C_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
	-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="%{optflags} -DNDEBUG" \
%endif
%if 0%{?__isa_bits} == 64
	-DLLVM_LIBDIR_SUFFIX=64 \
%else
	-DLLVM_LIBDIR_SUFFIX= \
%endif
	\
	-DLLVM_TARGETS_TO_BUILD="X86;AMDGPU;PowerPC;NVPTX;SystemZ;AArch64;ARM;Mips;BPF" \
	-DLLVM_ENABLE_LIBCXX:BOOL=OFF \
	-DLLVM_ENABLE_ZLIB:BOOL=ON \
	-DLLVM_ENABLE_FFI:BOOL=ON \
	-DLLVM_ENABLE_RTTI:BOOL=ON \
	-DSPHINX_WARNINGS_AS_ERRORS:BOOL=OFF \
%if %{with gold}
	-DLLVM_BINUTILS_INCDIR=%{_includedir} \
%endif
	\
	-DLLVM_BUILD_RUNTIME:BOOL=ON \
	\
	-DLLVM_INCLUDE_TOOLS:BOOL=ON \
	-DLLVM_BUILD_TOOLS:BOOL=ON \
	\
	-DLLVM_INCLUDE_TESTS:BOOL=ON \
	-DLLVM_BUILD_TESTS:BOOL=ON \
	\
	-DLLVM_INCLUDE_EXAMPLES:BOOL=ON \
	-DLLVM_BUILD_EXAMPLES:BOOL=OFF \
	\
	-DLLVM_INCLUDE_UTILS:BOOL=ON \
	-DLLVM_INSTALL_UTILS:BOOL=OFF \
	\
	-DLLVM_INCLUDE_DOCS:BOOL=ON \
	-DLLVM_BUILD_DOCS:BOOL=ON \
%if 0%{?fedora} >= 24
	-DLLVM_ENABLE_SPHINX:BOOL=ON \
%endif
	-DLLVM_ENABLE_DOXYGEN:BOOL=OFF \
	\
	-DLLVM_BUILD_LLVM_DYLIB:BOOL=ON \
	-DLLVM_DYLIB_EXPORT_ALL:BOOL=ON \
	-DLLVM_LINK_LLVM_DYLIB:BOOL=ON \
	-DLLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL=ON \
	-DLLVM_INSTALL_TOOLCHAIN_ONLY:BOOL=OFF \
	\
%if 0%{?fedora} >= 24
	-DSPHINX_EXECUTABLE=/usr/bin/sphinx-build-3
%endif

make %{?_smp_mflags}

%install
cd _build
make install DESTDIR=%{buildroot}

# fix multi-lib
mv -v %{buildroot}%{_bindir}/llvm-config{,-%{__isa_bits}}
mv -v %{buildroot}%{_includedir}/llvm/Config/llvm-config{,-%{__isa_bits}}.h
install -m 0644 %{SOURCE100} %{buildroot}%{_includedir}/llvm/Config/llvm-config.h

# Fix for the removals of alternatives
ln -s llvm-config-%{__isa_bits} %{buildroot}%{_bindir}/llvm-config

mkdir -p %{buildroot}/etc/ld.so.conf.d
echo %{_prefix}/lib64 > %{buildroot}/etc/ld.so.conf.d/%{name}.conf

%check
cd _build
make check-all || :

%files
%{_bindir}/*
%{_datadir}/opt-viewer
%if 0%{?fedora} >= 24
%{_mandir}/man1/*.1
%endif
%exclude %{_bindir}/llvm-config
%exclude %{_bindir}/llvm-config-%{__isa_bits}
%if 0%{?fedora} >= 24
%exclude %{_mandir}/man1/llvm-config.1
%endif

%files libs
%{_libdir}/BugpointPasses.so
%{_libdir}/LLVMHello.so
%if %{with gold}
%{_libdir}/LLVMgold.so
%endif
%{_libdir}/libLLVM-5.0*.so
%{_libdir}/libLTO.so
%{_libdir}/libLTO.so.*
/etc/ld.so.conf.d/%{name}.conf

%files devel
%{_bindir}/llvm-config
%{_bindir}/llvm-config-%{__isa_bits}
%if 0%{?fedora} >= 24
%{_mandir}/man1/llvm-config.1
%endif
%{_includedir}/llvm
%{_includedir}/llvm-c
%{_libdir}/libLLVM.so
%{_libdir}/cmake/llvm

%files doc
%if 0%{?fedora} >= 24
%doc %{_pkgdocdir}/html
%endif

%files static
%{_libdir}/*.a

%changelog
* Tue Nov 29 2016 Josh Stone <jistone@redhat.com> - 3.9.0-7
- Apply backports from rust-lang/llvm#55, #57

* Tue Nov 01 2016 Dave Airlie <airlied@gmail.com - 3.9.0-6
- rebuild for new arches

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-5
- apply the patch from -4

* Wed Oct 26 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-4
- add fix for lldb out-of-tree build

* Mon Oct 17 2016 Josh Stone <jistone@redhat.com> - 3.9.0-3
- Apply backports from rust-lang/llvm#47, #48, #53, #54

* Sat Oct 15 2016 Josh Stone <jistone@redhat.com> - 3.9.0-2
- Apply an InstCombine backport via rust-lang/llvm#51

* Wed Sep 07 2016 Dave Airlie <airlied@redhat.com> - 3.9.0-1
- llvm 3.9.0
- upstream moved where cmake files are packaged.
- upstream dropped CppBackend

* Wed Jul 13 2016 Adam Jackson <ajax@redhat.com> - 3.8.1-1
- llvm 3.8.1
- Add mips target
- Fix some shared library mispackaging

* Tue Jun 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> - 3.8.0-2
- fix color support detection on terminal

* Thu Mar 10 2016 Dave Airlie <airlied@redhat.com> 3.8.0-1
- llvm 3.8.0 release

* Wed Mar 09 2016 Dan Horák <dan[at][danny.cz> 3.8.0-0.3
- install back memory consumption workaround for s390

* Thu Mar 03 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.2
- llvm 3.8.0 rc3 release

* Fri Feb 19 2016 Dave Airlie <airlied@redhat.com> 3.8.0-0.1
- llvm 3.8.0 rc2 release

* Tue Feb 16 2016 Dan Horák <dan[at][danny.cz> 3.7.1-7
- recognize s390 as SystemZ when configuring build

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-6
- export C++ API for mesa.

* Sat Feb 13 2016 Dave Airlie <airlied@redhat.com> 3.7.1-5
- reintroduce llvm-static, clang needs it currently.

* Fri Feb 12 2016 Dave Airlie <airlied@redhat.com> 3.7.1-4
- jump back to single llvm library, the split libs aren't working very well.

* Fri Feb 05 2016 Dave Airlie <airlied@redhat.com> 3.7.1-3
- add missing obsoletes (#1303497)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 07 2016 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.1-1
- new upstream release
- enable gold linker

* Wed Nov 04 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- fix Requires for subpackages on the main package

* Tue Oct 06 2015 Jan Vcelak <jvcelak@fedoraproject.org> 3.7.0-100
- initial version using cmake build system
