import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function PrivacyPage() {
  return (
    <PageContainer
      title="Gizlilik politikası"
      subtitle="Kahvesiz Çalışma içinde işlenen kullanıcı verilerinin kapsam özeti."
    >
      <Card>
        <p class="paragraph">
          Bu metin, uygulama içinde işlenen verilerin kapsamını ve kullanım amacını özetler. Uygulamayı kullanarak
          bu politikayı kabul etmiş sayılırsınız.
        </p>

        <div class="policy-section">
          <p class="policy-section__title">Toplanan veriler</p>
          <ul class="simple-list">
            <li>İsim ve e-posta adresi</li>
            <li>Parola hash bilgisi (düz metin parola tutulmaz)</li>
            <li>Doğrulama ve oturum süreçlerine ait teknik veriler</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Kullanım amaçları</p>
          <ul class="simple-list">
            <li>Hesap oluşturma, giriş ve e-posta doğrulama akışlarını yürütmek</li>
            <li>Kafe içeriklerini ve rol/yetki yönetimini sürdürmek</li>
            <li>Güvenlik ve kötüye kullanım önlemlerini uygulamak</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Saklama ve güvenlik</p>
          <p class="paragraph paragraph--compact">
            Veriler uygulamanın çalışması için gerekli olduğu sürece saklanır. Erişim kontrolleri, parola hashleme ve
            CSRF koruması gibi mekanizmalar güvenliği destekler.
          </p>
        </div>

        <p class="paragraph paragraph--compact">
          Talepleriniz için <A class="ui-link" href="/contact">iletişim</A> sayfasını kullanabilirsiniz.
        </p>
      </Card>
    </PageContainer>
  );
}
