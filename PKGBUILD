# Maintainer: Your Name <your.email@example.com>
pkgname=zephyr-voice-input
pkgver=0.1.0
pkgrel=1
pkgdesc="Push-to-talk voice input for Linux using OpenAI Whisper"
arch=('any')
url="https://github.com/yourusername/zephyr"
license=('MIT')
depends=(
    'python>=3.11'
    'python-pip'
    'portaudio'
    'gtk4'
    'python-gobject'
    'python-yaml'
    'python-numpy'
    'python-pyaudio'
    'python-pynput'
    'python-xlib'
    'python-evdev'
    'python-watchdog'
)
makedepends=(
    'python-setuptools'
    'python-build'
    'python-installer'
    'python-wheel'
)
optdepends=(
    'python-noisereduce: Improved audio quality in noisy environments'
    'cuda: GPU acceleration for faster transcription'
    'whisper.cpp: Faster transcription performance with C++ implementation'
)
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')
install=zephyr.install

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Install Python package
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install systemd user service
    install -Dm644 zephyr.service \
        "$pkgdir/usr/lib/systemd/user/zephyr.service"
    
    # Install default configuration
    install -Dm644 config/default.yaml \
        "$pkgdir/etc/zephyr/config.yaml"
    
    # Install license
    install -Dm644 LICENSE \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    
    # Install documentation
    install -Dm644 README.md \
        "$pkgdir/usr/share/doc/$pkgname/README.md"
}
