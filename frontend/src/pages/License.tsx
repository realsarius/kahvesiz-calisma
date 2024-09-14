const License = () => {
    return (
        <div className="py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold mb-6">Lisans Bilgileri</h1>
                <p className="text-lg mb-4">
                    Bu sayfa, kişisel bir proje olan ve Berkan Sözer tarafından geliştirilen projenin lisans bilgilerini ve
                    kullanım şartlarını açıklar. Projemizi kullanmadan önce bu bilgileri dikkatlice okumanız önemlidir.
                </p>
                <h2 className="text-2xl font-semibold mb-4">Lisans Türü</h2>
                <p className="text-lg mb-4">
                    Bu proje, <strong>MIT Lisansı</strong> altında lisanslanmıştır. MIT Lisansı, açık kaynaklı yazılımlar
                    için oldukça yaygın bir lisans türüdür ve projelerin serbestçe kullanılmasına, değiştirilmesine ve
                    dağıtılmasına izin verir.
                </p>
                <h2 className="text-2xl font-semibold mb-4">Lisans Koşulları</h2>
                <p className="text-lg mb-4">
                    MIT Lisansı kapsamında proje şu şartlara tabidir:
                </p>
                <ul className="list-disc pl-5 mb-4">
                    <li>Yazılımın orijinal kopyasıyla birlikte lisans metninin ve telif hakkı bildirisinin sağlanması
                        gerekir.
                    </li>
                    <li>Yazılımın kullanımı, değiştirilmesi ve dağıtılması serbesttir, ancak yazılımın her kopyasında lisans
                        metni ve telif hakkı bildirimi korunmalıdır.
                    </li>
                    <li>Yazılım, herhangi bir garanti olmaksızın sağlanır. Geliştirici, yazılımın kullanımından doğabilecek
                        herhangi bir zarardan sorumlu değildir.
                    </li>
                </ul>
                <h2 className="text-2xl font-semibold mb-4">Telif Hakları ve İletişim</h2>
                <p className="text-lg mb-4">
                    Proje, <strong>Berkan Sözer</strong> tarafından geliştirilmiştir. Herhangi bir lisans veya proje ile
                    ilgili sorunuz varsa, bizimle iletişime geçebilirsiniz.
                </p>
                <ul className="list-disc pl-5 mb-4">
                    <li>E-posta: <a href="mailto:berkansozer@outlook.com" className="text-lavender hover:underline">berkansozer@outlook.com</a>
                    </li>
                </ul>
                <h2 className="text-2xl font-semibold mb-4">Lisans Metni</h2>
                <p className="text-lg mb-4">
                    Aşağıda MIT Lisansı'nın tam metnini bulabilirsiniz:
                </p>
                <pre className="p-4 rounded-lg border border-gray-200 overflow-x-auto">
      MIT License{'\n'}
      Copyright (c) 2024 Berkan Sözer{'\n'}
      İzni verilenler: Yazılımın kopyalarını kullanabilir, kopyalayabilir, değiştirebilir,
      birleştirebilir, yayınlayabilir, dağıtabilir, yeniden lisanslayabilir veya satabilirsiniz.
      {'\n'}
      Yukarıdaki telif hakkı bildirimi ve bu izin bildirimi, yazılımın tüm kopyalarında bulunmalıdır.{'\n'}
      YAZILIM, HERHANGİ BİR GARANTİ OLMADAN SAĞLANMAKTADIR. KULLANIMINDAN DOĞABİLECEK HERHANGİ BİR ZARARDAN SORUMLU DEĞİLDİR.
                </pre>
            </div>
        </div>
    );
};

export default License;
