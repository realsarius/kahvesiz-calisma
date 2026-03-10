import { A } from "@solidjs/router";
import { Card } from "../components/ui/Card";
import { PageContainer } from "../components/ui/PageContainer";

export default function PrivacyPage() {
  return (
    <PageContainer
      title="Gizlilik politikasi"
      subtitle="Kahvesiz Calisma icinde islenen kullanici verilerinin kapsam ozeti."
    >
      <Card>
        <p class="paragraph">
          Bu metin, uygulama icinde islenen verilerin kapsamini ve kullanim amacini ozetler. Uygulamayi
          kullanarak bu politikayi kabul etmis sayilirsiniz.
        </p>

        <div class="policy-section">
          <p class="policy-section__title">Toplanan veriler</p>
          <ul class="simple-list">
            <li>Isim ve e-posta adresi</li>
            <li>Parola hash bilgisi (duz metin parola tutulmaz)</li>
            <li>Dogrulama ve oturum sureclerine ait teknik veriler</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Kullanim amaclari</p>
          <ul class="simple-list">
            <li>Hesap olusturma, login ve e-posta dogrulama akislarini yurutmek</li>
            <li>Kafe iceriklerini ve rol/yetki yonetimini surdurmek</li>
            <li>Guvenlik ve kotuye kullanim onlemlerini uygulamak</li>
          </ul>
        </div>

        <div class="policy-section">
          <p class="policy-section__title">Saklama ve guvenlik</p>
          <p class="paragraph paragraph--compact">
            Veriler uygulamanin calismasi icin gerekli oldugu surece saklanir. Erisim kontrolleri,
            parola hashleme ve CSRF korumasi gibi mekanizmalar guvenligi destekler.
          </p>
        </div>

        <p class="paragraph paragraph--compact">
          Talepleriniz icin <A class="ui-link" href="/contact">iletisim</A> sayfasini kullanabilirsiniz.
        </p>
      </Card>
    </PageContainer>
  );
}
