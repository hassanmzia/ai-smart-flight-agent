import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';
import { GlobeAltIcon, SparklesIcon, UsersIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

const AboutPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            About AI Travel Agent
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            Your intelligent companion for seamless travel planning and booking
          </p>
        </div>

        {/* Mission Statement */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="text-center">Our Mission</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-700 dark:text-gray-300 text-center leading-relaxed">
              At AI Travel Agent, we're revolutionizing the way people plan and book their travels.
              By combining cutting-edge artificial intelligence with comprehensive travel data,
              we make it easier than ever to find the perfect flights, hotels, and experiences
              tailored to your unique preferences and budget.
            </p>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <Card hover>
            <CardContent className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/30 dark:to-blue-800/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <SparklesIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                AI-Powered Intelligence
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Our advanced AI analyzes millions of options to find the best deals and
                recommendations personalized just for you.
              </p>
            </CardContent>
          </Card>

          <Card hover>
            <CardContent className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-green-200 dark:from-green-900/30 dark:to-green-800/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <GlobeAltIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                Global Coverage
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Access to thousands of destinations, flights, hotels, and experiences
                worldwide, all in one platform.
              </p>
            </CardContent>
          </Card>

          <Card hover>
            <CardContent className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-purple-200 dark:from-purple-900/30 dark:to-purple-800/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <UsersIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                Customer-Centric
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Your satisfaction is our priority. We provide 24/7 support and
                personalized assistance throughout your journey.
              </p>
            </CardContent>
          </Card>

          <Card hover>
            <CardContent className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-100 to-orange-200 dark:from-orange-900/30 dark:to-orange-800/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <ShieldCheckIcon className="h-8 w-8 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                Secure & Trusted
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Your data and transactions are protected with enterprise-grade security
                and encryption standards.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Story Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-center">Our Story</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                AI Travel Agent was founded with a simple yet ambitious vision: to make travel
                planning effortless and enjoyable for everyone. We recognized that finding the
                perfect trip often meant spending hours comparing options across multiple websites,
                dealing with confusing interfaces, and missing out on better deals.
              </p>
              <p className="text-gray-700 dark:text-gray-300 mb-4">
                By leveraging the latest advancements in artificial intelligence and machine learning,
                we've created a platform that does the heavy lifting for you. Our intelligent system
                learns from your preferences, understands your priorities, and presents you with
                options that truly match your needs.
              </p>
              <p className="text-gray-700 dark:text-gray-300">
                Today, we're proud to serve thousands of travelers worldwide, helping them discover
                new destinations, save money, and create unforgettable memories. Join us on this
                journey and experience the future of travel planning.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AboutPage;
