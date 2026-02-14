import { Helmet } from "react-helmet-async";

export default function PrivacyPolicy() {
  return (
    <>
      <Helmet>
        <title>Privacy Policy - OpenMercura</title>
      </Helmet>
      
      <div className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-gray-600 mb-8">Last updated: February 14, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">1. Information We Collect</h2>
          <p className="text-gray-700 mb-4">
            We collect information you provide directly to us, including:
          </p>
          <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
            <li>Name and email address</li>
            <li>Company information</li>
            <li>Phone number (optional)</li>
            <li>Customer data you upload to our CRM</li>
            <li>Payment information (processed securely by Paddle)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">2. How We Use Your Information</h2>
          <p className="text-gray-700 mb-4">
            We use your information to:
          </p>
          <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
            <li>Provide and maintain the OpenMercura service</li>
            <li>Send transactional emails (quotes, notifications)</li>
            <li>Process payments and manage subscriptions</li>
            <li>Improve our product and user experience</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">3. Analytics and Cookies</h2>
          <p className="text-gray-700 mb-4">
            We use PostHog for analytics to understand how users interact with our platform. 
            We use essential cookies for authentication and session management.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">4. Data Sharing</h2>
          <p className="text-gray-700 mb-4">
            We do not sell your personal data. We share data only with:
          </p>
          <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
            <li><strong>Paddle:</strong> For subscription billing</li>
            <li><strong>Supabase:</strong> For secure data storage</li>
            <li><strong>PostHog:</strong> For product analytics</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">5. Data Security</h2>
          <p className="text-gray-700 mb-4">
            We implement industry-standard security measures including encryption at rest and 
            in transit. Your data is stored securely in Supabase with row-level security.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">6. Your Rights</h2>
          <p className="text-gray-700 mb-4">
            You have the right to access, correct, or delete your personal data. 
            Contact us at support@openmercura.com to exercise these rights.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">7. Changes to This Policy</h2>
          <p className="text-gray-700 mb-4">
            We may update this policy from time to time. We will notify you of significant 
            changes via email or in-app notification.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">8. Contact Us</h2>
          <p className="text-gray-700">
            For privacy-related questions, contact: support@openmercura.com
          </p>
        </section>
      </div>
    </>
  );
}
