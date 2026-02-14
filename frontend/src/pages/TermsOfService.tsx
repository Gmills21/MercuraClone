import { Helmet } from "react-helmet-async";

export default function TermsOfService() {
  return (
    <>
      <Helmet>
        <title>Terms of Service - OpenMercura</title>
      </Helmet>
      
      <div className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-600 mb-8">Last updated: February 14, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">1. Acceptance of Terms</h2>
          <p className="text-gray-700 mb-4">
            By accessing or using OpenMercura, you agree to be bound by these Terms of Service. 
            If you do not agree, do not use our service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">2. Description of Service</h2>
          <p className="text-gray-700 mb-4">
            OpenMercura is a CRM and quoting platform for B2B sales teams. We provide tools for 
            customer management, quote generation, and ERP integration.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">3. Account Registration</h2>
          <p className="text-gray-700 mb-4">
            You must provide accurate information when creating an account. You are responsible 
            for maintaining the security of your account credentials.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">4. Subscription and Payment</h2>
          <p className="text-gray-700 mb-4">
            OpenMercura is offered on a subscription basis. Fees are billed in advance and are 
            non-refundable. You may cancel your subscription at any time through your account settings.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">5. Data Ownership</h2>
          <p className="text-gray-700 mb-4">
            You retain ownership of all data you input into OpenMercura. We claim no rights to 
            your customer information, quotes, or business data.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">6. Acceptable Use</h2>
          <p className="text-gray-700 mb-4">
            You may not use OpenMercura for illegal activities, to send spam, or to infringe on 
            others' rights. We reserve the right to suspend accounts violating these terms.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">7. Limitation of Liability</h2>
          <p className="text-gray-700 mb-4">
            OpenMercura is provided "as is" without warranties. Our liability is limited to 
            the amount you paid for service in the past 12 months.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">8. Contact</h2>
          <p className="text-gray-700">
            For questions about these terms, contact: support@openmercura.com
          </p>
        </section>
      </div>
    </>
  );
}
