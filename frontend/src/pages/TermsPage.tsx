import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';

const TermsPage = () => {
  const lastUpdated = 'February 11, 2026';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Terms of Service
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Last updated: {lastUpdated}
          </p>
        </div>

        <Card className="prose dark:prose-invert max-w-none">
          <CardContent>
            <div className="space-y-8">
              {/* Introduction */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  1. Introduction
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  Welcome to AI Travel Agent. These Terms of Service ("Terms") govern your use of our
                  website and services. By accessing or using our platform, you agree to be bound by
                  these Terms. If you do not agree to these Terms, please do not use our services.
                </p>
              </section>

              {/* Services */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  2. Services
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  AI Travel Agent provides an online platform for searching, comparing, and booking
                  travel services including flights, hotels, and other travel-related products. We act
                  as an intermediary between you and travel service providers.
                </p>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  We reserve the right to modify, suspend, or discontinue any part of our services
                  at any time without prior notice.
                </p>
              </section>

              {/* User Accounts */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  3. User Accounts
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  To use certain features of our platform, you may need to create an account. You agree to:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Provide accurate, current, and complete information</li>
                  <li>Maintain and update your information to keep it accurate</li>
                  <li>Keep your password secure and confidential</li>
                  <li>Notify us immediately of any unauthorized access to your account</li>
                  <li>Accept responsibility for all activities that occur under your account</li>
                </ul>
              </section>

              {/* Bookings and Payments */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  4. Bookings and Payments
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  When you make a booking through our platform:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>You enter into a contract with the service provider (airline, hotel, etc.)</li>
                  <li>Prices are subject to availability and may change until booking is confirmed</li>
                  <li>All payments must be made in full at the time of booking unless otherwise stated</li>
                  <li>Cancellation and modification policies vary by provider</li>
                  <li>Additional fees may apply for changes or cancellations</li>
                </ul>
              </section>

              {/* Prohibited Conduct */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  5. Prohibited Conduct
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  You agree not to:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Use the platform for any illegal or unauthorized purpose</li>
                  <li>Attempt to gain unauthorized access to our systems or other users' accounts</li>
                  <li>Interfere with or disrupt the platform or servers</li>
                  <li>Use automated systems or software to extract data from our platform</li>
                  <li>Impersonate another person or entity</li>
                  <li>Post or transmit malicious code or viruses</li>
                </ul>
              </section>

              {/* Intellectual Property */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  6. Intellectual Property
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  All content on our platform, including text, graphics, logos, images, and software,
                  is the property of AI Travel Agent or its licensors and is protected by copyright,
                  trademark, and other intellectual property laws. You may not reproduce, distribute,
                  modify, or create derivative works without our express written permission.
                </p>
              </section>

              {/* Disclaimers */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  7. Disclaimers
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  Our platform is provided "as is" and "as available" without warranties of any kind.
                  We do not guarantee:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Uninterrupted or error-free operation of the platform</li>
                  <li>Accuracy, completeness, or timeliness of information</li>
                  <li>Availability of any particular travel service or price</li>
                  <li>The quality of services provided by third-party providers</li>
                </ul>
              </section>

              {/* Limitation of Liability */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  8. Limitation of Liability
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  To the maximum extent permitted by law, AI Travel Agent shall not be liable for any
                  indirect, incidental, special, consequential, or punitive damages resulting from
                  your use of or inability to use our services, including but not limited to lost
                  profits, data loss, or business interruption.
                </p>
              </section>

              {/* Changes to Terms */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  9. Changes to Terms
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  We reserve the right to modify these Terms at any time. We will notify you of
                  significant changes by posting a notice on our platform or sending you an email.
                  Your continued use of the platform after such modifications constitutes acceptance
                  of the updated Terms.
                </p>
              </section>

              {/* Contact */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  10. Contact Information
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  If you have any questions about these Terms, please contact us at:
                  <br />
                  Email: legal@aitravelagent.com
                  <br />
                  Address: 123 Travel Street, San Francisco, CA 94102
                </p>
              </section>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TermsPage;
