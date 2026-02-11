import { useState } from 'react';
import { Card, CardContent } from '@/components/common';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const FAQPage = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const faqs: FAQItem[] = [
    {
      category: 'General',
      question: 'What is AI Travel Agent?',
      answer: 'AI Travel Agent is an intelligent travel planning platform that uses artificial intelligence to help you find the best flights, hotels, and experiences tailored to your preferences and budget. Our AI analyzes millions of options to provide personalized recommendations.',
    },
    {
      category: 'General',
      question: 'How does the AI recommendation system work?',
      answer: 'Our AI system analyzes your search preferences, budget, travel dates, and other factors to provide personalized recommendations. It learns from your choices and feedback to continuously improve suggestions for future trips.',
    },
    {
      category: 'Booking',
      question: 'How do I book a flight or hotel?',
      answer: 'Simply search for your destination and dates, browse the results, and click on your preferred option. Follow the booking process to enter your details and complete the payment. You\'ll receive a confirmation email with all the details.',
    },
    {
      category: 'Booking',
      question: 'Can I modify or cancel my booking?',
      answer: 'Yes, you can modify or cancel most bookings through your dashboard. However, modification and cancellation policies vary by airline and hotel. Please review the specific terms before making changes, as fees may apply.',
    },
    {
      category: 'Booking',
      question: 'Is my payment information secure?',
      answer: 'Absolutely! We use industry-standard encryption and security measures to protect your payment information. We never store your complete credit card details on our servers.',
    },
    {
      category: 'Account',
      question: 'Do I need to create an account to book?',
      answer: 'While you can browse without an account, creating one allows you to save your preferences, track bookings, receive price alerts, and access your trip history.',
    },
    {
      category: 'Account',
      question: 'How do I reset my password?',
      answer: 'Click on "Sign In" and then "Forgot Password". Enter your email address, and we\'ll send you instructions to reset your password.',
    },
    {
      category: 'Prices',
      question: 'Are the prices shown final?',
      answer: 'The prices displayed include most fees and taxes. However, some airlines may charge additional fees for baggage, seat selection, or other services. These will be clearly shown before you complete your booking.',
    },
    {
      category: 'Prices',
      question: 'Can I set up price alerts?',
      answer: 'Yes! When viewing search results, click on "Set Price Alert" for any flight or hotel. We\'ll notify you when prices drop or when deals matching your criteria become available.',
    },
    {
      category: 'Support',
      question: 'How can I contact customer support?',
      answer: 'You can reach our support team via email at support@aitravelagent.com, through the contact form on our Contact page, or by calling our phone number during business hours. We typically respond within 24 hours.',
    },
    {
      category: 'Support',
      question: 'What if I encounter issues during my trip?',
      answer: 'Our support team is available 24/7 for urgent travel issues. You can access emergency support through your booking confirmation email or by logging into your account and viewing your active bookings.',
    },
    {
      category: 'Features',
      question: 'What destinations do you cover?',
      answer: 'We cover destinations worldwide, with access to thousands of flights and hotels. Our AI can help you plan trips to major cities, remote locations, and everything in between.',
    },
    {
      category: 'Features',
      question: 'Can AI Travel Agent help plan multi-city trips?',
      answer: 'Yes! Our platform supports complex itineraries including multi-city trips. Use the AI Planner feature to create detailed trip plans with multiple destinations, accommodations, and activities.',
    },
  ];

  const categories = ['All', ...Array.from(new Set(faqs.map(faq => faq.category)))];

  const filteredFAQs = selectedCategory === 'All'
    ? faqs
    : faqs.filter(faq => faq.category === selectedCategory);

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Frequently Asked Questions
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Find answers to common questions about AI Travel Agent
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 justify-center mb-8">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedCategory === category
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* FAQ List */}
        <div className="space-y-4">
          {filteredFAQs.map((faq, index) => (
            <Card key={index} className="overflow-hidden">
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full text-left p-6 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex-1">
                  <span className="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 mb-2">
                    {faq.category}
                  </span>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {faq.question}
                  </h3>
                </div>
                <ChevronDownIcon
                  className={`h-5 w-5 text-gray-500 transition-transform flex-shrink-0 ml-4 ${
                    openIndex === index ? 'transform rotate-180' : ''
                  }`}
                />
              </button>
              {openIndex === index && (
                <CardContent className="pt-0 pb-6 px-6">
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    {faq.answer}
                  </p>
                </CardContent>
              )}
            </Card>
          ))}
        </div>

        {/* Contact CTA */}
        <Card className="mt-12 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-800">
          <CardContent className="text-center py-8">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Still have questions?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Our support team is here to help you with any questions or concerns.
            </p>
            <a
              href="/contact"
              className="inline-block px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold"
            >
              Contact Support
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FAQPage;
