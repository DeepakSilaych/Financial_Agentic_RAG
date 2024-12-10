import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform, useAnimation, useInView } from 'framer-motion';
import { ArrowRight, FileText, MessageSquare, Search, Shield, ChevronDown, BotMessageSquare } from 'lucide-react';

// Import your logo
import Logo from '../assets/logo.svg';

const ScrollIndicator = () => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 1, repeat: Infinity, repeatType: "reverse" }}
    className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-blue-600"
  >
    <ChevronDown size={32} />
  </motion.div>
);

const FeatureCard = ({ icon: Icon, title, description }) => {
  const controls = useAnimation();
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true, margin: "50px" });

  useEffect(() => {
    if (inView) {
      controls.start({ opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } });
    }
  }, [controls, inView]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={controls}
      whileHover={{ y: -5, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)" }}
      transition={{ duration: 0.3 }}
      className="p-8 bg-white rounded-2xl shadow-lg border border-gray-100 backdrop-blur-sm bg-white/90 hover:border-blue-200"
    >
      <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl flex items-center justify-center mb-6 transform transition-transform group-hover:scale-110">
        <Icon className="w-7 h-7 text-blue-600" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{description}</p>
    </motion.div>
  );
};

const BenefitCard = ({ title, description, stat, statText }) => {
  const controls = useAnimation();
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (inView) {
      controls.start({ opacity: 1, y: 0, transition: { duration: 0.8 } });
    }
  }, [controls, inView]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      className="relative p-8 rounded-2xl bg-white shadow-xl border border-gray-100"
    >
      <div className="absolute top-0 right-0 -mt-4 mr-4">
        <div className="bg-blue-50 rounded-lg px-4 py-2">
          <span className="text-2xl font-bold text-blue-600">{stat}</span>
        </div>
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>
      <p className="text-sm font-medium text-blue-600">{statText}</p>
    </motion.div>
  );
};

const VideoSection = ({ src, title, description, reverse }) => {
  const controls = useAnimation();
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true, margin: "100px" });

  useEffect(() => {
    if (inView) {
      controls.start({ opacity: 1, x: 0, transition: { duration: 1, ease: "easeOut" } });
    }
  }, [controls, inView]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: reverse ? 50 : -50 }}
      animate={controls}
      className={`flex flex-col ${reverse ? 'md:flex-row-reverse' : 'md:flex-row'} items-center gap-12 py-20`}
    >
      <div className="flex-1">
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl overflow-hidden shadow-2xl border border-blue-500/20 transform transition-transform hover:scale-[1.02]">
          <video
            className="w-full aspect-video object-cover opacity-90 hover:opacity-100 transition-opacity"
            autoPlay
            loop
            muted
            playsInline
          >
            <source src={src} type="video/mp4" />
          </video>
        </div>
      </div>
      <div className="flex-1 space-y-6">
        <h3 className="text-4xl font-bold text-gray-900 leading-tight">{title}</h3>
        <p className="text-xl text-gray-600 leading-relaxed">{description}</p>
        <motion.div
          whileHover={{ x: 10 }}
          className="inline-flex items-center text-blue-600 font-medium"
        >
          Learn more <ArrowRight className="ml-2 w-5 h-5" />
        </motion.div>
      </div>
    </motion.div>
  );
};

const LandingPage = () => {
  const { scrollYProgress } = useScroll();
  const backgroundY = useTransform(scrollYProgress, [0, 1], ['0%', '30%']);

  const features = [
    {
      icon: FileText,
      title: 'Smart Document Management',
      description: 'Upload and organize your documents with AI-powered categorization. Supports PDFs, Word docs, and more.'
    },
    {
      icon: MessageSquare,
      title: 'Interactive Chat',
      description: 'Have natural conversations with your documents. Get instant answers and insights from your content.'
    },
    {
      icon: Search,
      title: 'Semantic Search',
      description: 'Find exactly what you need with context-aware search that understands meaning, not just keywords.'
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Your documents are encrypted and secure. We prioritize data privacy and compliance.'
    }
  ];

  const benefits = [
    {
      title: "Save Hours of Time",
      description: "Stop manually searching through documents. Our AI instantly finds the information you need.",
      stat: "85%",
      statText: "reduction in search time"
    },
    {
      title: "Enhance Productivity",
      description: "Focus on high-value work while AI handles document analysis and information retrieval.",
      stat: "3x",
      statText: "faster document processing"
    },
    {
      title: "Better Insights",
      description: "Discover connections and insights across your document library that you might have missed.",
      stat: "100%",
      statText: "accurate responses"
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <div className="min-h-screen relative overflow-hidden">
        {/* Animated background */}
        <motion.div
          style={{ y: backgroundY }}
          className="absolute inset-0 bg-gradient-to-b from-gray-50 via-white to-blue-50 -z-10"
        />

        {/* Hero Section */}
        <div className="min-h-screen flex flex-col justify-center relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center"
            >
              {/* Hero Content */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.8 }}
                className="max-w-4xl mx-auto"
              >
                {/* Badge */}
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.6 }}
                  className="inline-flex items-center px-4 py-2 rounded-full bg-blue-50 mb-8"
                >
                  <span className="text-blue-600 font-medium text-sm">
                    🚀 Powered by Advanced AI Technology
                  </span>
                </motion.div>

                {/* Main Heading */}
                <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
                  Transform Your
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                    {' '}Document Experience{' '}
                  </span>
                  with AI
                </h1>

                {/* Subheading */}
                <p className="text-xl md:text-2xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
                  Upload, search, and chat with your documents using state-of-the-art AI technology.
                  Experience seamless document management like never before.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Link
                    to="/app"
                    className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-all transform hover:scale-105 duration-200 shadow-lg hover:shadow-xl"
                  >
                    Get Started Free
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <a
                    href="#demo"
                    className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 text-lg font-medium text-gray-900 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 transition-all transform hover:scale-105 duration-200"
                  >
                    Watch Demo
                    <motion.div
                      animate={{ y: [0, 5, 0] }}
                      transition={{ repeat: Infinity, duration: 2 }}
                      className="ml-2"
                    >
                      ↓
                    </motion.div>
                  </a>
                </div>

                {/* Trust Badges */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.8, duration: 0.8 }}
                  className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 items-center justify-items-center"
                >
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900 mb-1">10k+</div>
                    <div className="text-sm text-gray-600">Active Users</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900 mb-1">1M+</div>
                    <div className="text-sm text-gray-600">Documents Processed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900 mb-1">99.9%</div>
                    <div className="text-sm text-gray-600">Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-gray-900 mb-1">24/7</div>
                    <div className="text-sm text-gray-600">Support</div>
                  </div>
                </motion.div>
              </motion.div>
            </motion.div>
          </div>

          {/* Background Decorations */}
          <div className="absolute inset-0 z-0">
            <div className="absolute top-1/4 left-0 w-72 h-72 bg-blue-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
            <div className="absolute top-1/3 right-0 w-72 h-72 bg-purple-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-1/4 left-1/4 w-72 h-72 bg-yellow-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
          </div>

          <ScrollIndicator />
        </div>

        {/* Features Section */}
        <section className="py-20 bg-gradient-to-b from-white to-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-4xl font-bold text-gray-900 mb-4"
              >
                Powerful Features
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-xl text-gray-600 max-w-3xl mx-auto"
              >
                Everything you need to manage and interact with your documents intelligently
              </motion.p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <FeatureCard key={index} {...feature} />
              ))}
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-4xl font-bold text-gray-900 mb-4"
              >
                Why Choose Us
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-xl text-gray-600 max-w-3xl mx-auto"
              >
                Experience the benefits of AI-powered document management
              </motion.p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {benefits.map((benefit, index) => (
                <BenefitCard key={index} {...benefit} />
              ))}
            </div>
          </div>
        </section>

        {/* Demo Section */}
        <div className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ margin: "100px" }}
              transition={{ duration: 1.2 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                See FinSight in Action
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Watch how FinSight transforms document interaction into an intuitive, AI-powered experience.
              </p>
            </motion.div>

            <VideoSection
              src="/path/to/your/chat-demo.mp4"
              title="Natural Document Conversations"
              description="Experience fluid, context-aware interactions with your documents. Our AI understands complex queries and provides accurate, relevant responses instantly."
              reverse={false}
            />

            <VideoSection
              src="/path/to/your/search-demo.mp4"
              title="Intelligent Search & Analysis"
              description="Find exactly what you're looking for with our semantic search engine. Discover insights and connections across your entire document library."
              reverse={true}
            />
          </div>
        </div>

        {/* Testimonials Section */}
        <div className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ margin: "100px" }}
              transition={{ duration: 1.2 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Loved by Teams Worldwide
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                See what professionals are saying about their experience with FinSight.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  quote: "FinSight has completely transformed how we handle documentation. The AI-powered search is a game-changer.",
                  author: "Sarah Chen",
                  role: "Technical Lead, TechCorp"
                },
                {
                  quote: "The natural language interface makes finding information in our docs incredibly fast and intuitive.",
                  author: "Michael Rodriguez",
                  role: "Product Manager, InnovateCo"
                },
                {
                  quote: "We've cut our document processing time by 75%. The ROI was immediate and substantial.",
                  author: "Emily Thompson",
                  role: "Operations Director, GlobalTech"
                }
              ].map((testimonial, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ margin: "50px" }}
                  transition={{ duration: 1, delay: index * 0.2 }}
                  className="bg-white p-8 rounded-xl shadow-lg"
                >
                  <p className="text-gray-600 mb-6 italic">"{testimonial.quote}"</p>
                  <div className="font-bold text-gray-900">{testimonial.author}</div>
                  <div className="text-sm text-gray-500">{testimonial.role}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-b from-gray-900 to-gray-800 text-white py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ margin: "100px" }}
              transition={{ duration: 1.2 }}
              className="text-center"
            >
              <h2 className="text-4xl font-bold mb-6">
                Ready to Transform Your Document Workflow?
              </h2>
              <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Join thousands of professionals who are already experiencing the future of document management.
                Get started with FinSight today.
              </p>
              <Link
                to="/app"
                className="inline-flex items-center px-8 py-4 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Start Free Trial
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default LandingPage;
