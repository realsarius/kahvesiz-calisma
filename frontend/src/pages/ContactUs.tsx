const ContactUs = () => {
    return (
        <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto p-8 rounded-lg shadow-md">
                <h1 className="text-3xl font-bold mb-6">İletişim</h1>
                <p className="text-lg mb-4">
                    Herhangi bir sorunuz, öneriniz veya proje ile ilgili konular için bizimle iletişime geçmekten çekinmeyin.
                    Aşağıdaki iletişim bilgilerini kullanarak bize ulaşabilirsiniz.
                </p>
                <h2 className="text-2xl font-semibold mb-4">İletişim Bilgileri</h2>
                <ul className="list-disc pl-5 mb-4">
                    <li>E-posta: <a href="mailto:berkansozer@outlook.com" className="text-lavender hover:underline">berkansozer@outlook.com</a></li>
                    <li>Telefon: +90 555 555 5555</li>
                </ul>
                <h2 className="text-2xl font-semibold mb-4">Sosyal Medya</h2>
                <ul className="list-disc pl-5 mb-4">
                    <li>LinkedIn: <a href="https://linkedin.com/in/berkansozer" className="text-lavender hover:underline">linkedin.com/in/berkansozer</a></li>
                    <li>GitHub: <a href="https://github.com/berkansozer" className="text-lavender hover:underline">github.com/berkansozer</a></li>
                </ul>
                <p className="text-lg mb-4">
                    Size en kısa sürede geri dönüş yapacağız. Bize ulaşmak için iletişim formunu da kullanabilirsiniz.
                </p>
            </div>
        </div>
    );
};

export default ContactUs;
