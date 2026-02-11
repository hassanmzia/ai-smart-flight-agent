import { Card, CardContent } from '@/components/common';

const PrivacyPage = () => {
  const lastUpdated = 'February 11, 2026';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Privacy Policy
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
                  At AI Travel Agent, we take your privacy seriously. This Privacy Policy explains how
                  we collect, use, disclose, and safeguard your information when you use our platform.
                  By using our services, you agree to the collection and use of information in
                  accordance with this policy.
                </p>
              </section>

              {/* Information We Collect */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  2. Information We Collect
                </h2>

                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-6">
                  2.1 Personal Information
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  We may collect personal information that you provide to us, including:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Name, email address, and phone number</li>
                  <li>Billing and payment information</li>
                  <li>Passport and travel document information</li>
                  <li>Travel preferences and history</li>
                  <li>Account credentials</li>
                </ul>

                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-6">
                  2.2 Automatically Collected Information
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  When you use our platform, we automatically collect:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Device information (IP address, browser type, operating system)</li>
                  <li>Usage data (pages visited, time spent, click patterns)</li>
                  <li>Cookies and similar tracking technologies</li>
                  <li>Location data (if you grant permission)</li>
                </ul>
              </section>

              {/* How We Use Your Information */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  3. How We Use Your Information
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  We use the collected information for various purposes:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>To provide and maintain our services</li>
                  <li>To process your bookings and transactions</li>
                  <li>To send you booking confirmations and updates</li>
                  <li>To personalize your experience and provide recommendations</li>
                  <li>To improve our platform and develop new features</li>
                  <li>To communicate with you about promotions and offers</li>
                  <li>To detect and prevent fraud or security issues</li>
                  <li>To comply with legal obligations</li>
                </ul>
              </section>

              {/* Information Sharing */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  4. Information Sharing and Disclosure
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  We may share your information with:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li><strong>Travel Service Providers:</strong> Airlines, hotels, and other providers necessary to complete your bookings</li>
                  <li><strong>Payment Processors:</strong> To process your payments securely</li>
                  <li><strong>Service Providers:</strong> Third parties who assist us in operating our platform</li>
                  <li><strong>Legal Authorities:</strong> When required by law or to protect our rights</li>
                  <li><strong>Business Transfers:</strong> In connection with a merger, sale, or acquisition</li>
                </ul>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-3">
                  We do not sell your personal information to third parties for their marketing purposes.
                </p>
              </section>

              {/* Data Security */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  5. Data Security
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  We implement appropriate technical and organizational measures to protect your
                  personal information against unauthorized access, alteration, disclosure, or
                  destruction. This includes encryption, secure servers, and access controls. However,
                  no method of transmission over the internet is 100% secure, and we cannot guarantee
                  absolute security.
                </p>
              </section>

              {/* Cookies */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  6. Cookies and Tracking Technologies
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  We use cookies and similar tracking technologies to:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li>Remember your preferences and settings</li>
                  <li>Understand how you use our platform</li>
                  <li>Improve our services and user experience</li>
                  <li>Deliver relevant advertisements</li>
                </ul>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-3">
                  You can control cookies through your browser settings, but disabling cookies may
                  affect your ability to use certain features of our platform.
                </p>
              </section>

              {/* Your Rights */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  7. Your Privacy Rights
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                  You have the right to:
                </p>
                <ul className="list-disc pl-6 space-y-2 text-gray-700 dark:text-gray-300">
                  <li><strong>Access:</strong> Request a copy of your personal information</li>
                  <li><strong>Correction:</strong> Update or correct inaccurate information</li>
                  <li><strong>Deletion:</strong> Request deletion of your personal information</li>
                  <li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
                  <li><strong>Data Portability:</strong> Receive your data in a structured format</li>
                  <li><strong>Restriction:</strong> Request restriction of processing in certain cases</li>
                </ul>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-3">
                  To exercise these rights, please contact us at privacy@aitravelagent.com.
                </p>
              </section>

              {/* Data Retention */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  8. Data Retention
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  We retain your personal information for as long as necessary to provide our services,
                  comply with legal obligations, resolve disputes, and enforce our agreements. When we
                  no longer need your information, we will securely delete or anonymize it.
                </p>
              </section>

              {/* Children's Privacy */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  9. Children's Privacy
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  Our services are not directed to children under 13 years of age. We do not knowingly
                  collect personal information from children. If you become aware that a child has
                  provided us with personal information, please contact us immediately.
                </p>
              </section>

              {/* International Transfers */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  10. International Data Transfers
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  Your information may be transferred to and processed in countries other than your own.
                  These countries may have different data protection laws. We ensure appropriate
                  safeguards are in place to protect your information in accordance with this Privacy
                  Policy.
                </p>
              </section>

              {/* Changes to Policy */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  11. Changes to This Privacy Policy
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  We may update this Privacy Policy from time to time. We will notify you of any
                  significant changes by posting the new policy on this page and updating the "Last
                  updated" date. We encourage you to review this Privacy Policy periodically.
                </p>
              </section>

              {/* Contact */}
              <section>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  12. Contact Us
                </h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  If you have any questions about this Privacy Policy or our data practices, please
                  contact us at:
                  <br /><br />
                  <strong>Email:</strong> privacy@aitravelagent.com
                  <br />
                  <strong>Address:</strong> 123 Travel Street, San Francisco, CA 94102
                  <br />
                  <strong>Phone:</strong> +1 (555) 123-4567
                </p>
              </section>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PrivacyPage;
