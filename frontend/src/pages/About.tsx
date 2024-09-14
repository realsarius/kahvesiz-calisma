const About = () => {
    return (
        <div className="max-w-4xl mx-auto p-6 rounded-lg">
            <h1 className="text-3xl font-bold mb-4">Hakkımızda</h1>
            <p className="text-lg mb-4 relative">
                Bu site, kafelerde laptop ile çalışabilirliğinizi değerlendirmek için oluşturulmuştur. Kafelerde çalışma,
                birçok kişi için iş yaparken rahat bir ortam sağlayabilir ve aynı zamanda sosyal etkileşim imkanı sunar.
                Ancak, her kafe bu tür bir çalışma için uygun olmayabilir.
            </p>
            <p className="text-lg mb-4">
                Sitemiz, çeşitli kafeleri değerlendirmeye alarak, bunların iş yapmaya uygun olup olmadığını belirlemenize
                yardımcı olur. İyi bir çalışma ortamı için gerekli olan internet hızından, priz erişimine kadar birçok
                faktörü göz önünde bulundururuz. Böylece, işlerinizi en verimli şekilde yapabileceğiniz kafeleri kolayca
                bulabilirsiniz.
            </p>
            <p className="text-lg">
                Amacımız, kafelerde çalışmayı seven bireyler için ideal mekanları belirlemek ve onlara en uygun seçenekleri
                sunmaktır. İyi çalışmalar!
            </p>
            <img src="/src/assets/heart.png" alt="Icon" className="w-40 mx-auto"/>
        </div>
    );
};

export default About;
