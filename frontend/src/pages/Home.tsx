import React from 'react';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
    return (
        <div className="relative isolate px-6 pt-14 lg:px-8">
            <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
                <div className="hidden sm:mb-8 sm:flex sm:justify-center">
                    {/* Optional announcement or banner */}
                </div>
                <div className="text-center">
                    <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
                        Verimli Çalışma Alanları
                    </h1>
                    <p className="mt-6 text-lg leading-8">
                        Günümüzde iş yaparken verimliliği artırmak, doğru çalışma ortamını seçmekle başlar. Kafeler, hem
                        rahat bir atmosfer sunar hem de sosyal etkileşim imkanları sağlar. Ancak, herkes için uygun
                        olmayabilirler.
                    </p>
                    <div className="mt-10 flex items-center justify-center gap-x-6">
                        <Link
                            to="/login"
                            className="rounded-md dark:text-zinc-900 dark:bg-lavender dark:hover:bg-lavender/90 px-3.5 py-2.5 text-sm font-semibold"
                        >
                            Şimdi Başlayın
                        </Link>
                        <Link
                            to="/about"
                            className="text-sm font-semibold leading-6"
                        >
                            Daha fazla bilgi <span aria-hidden="true">→</span>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
