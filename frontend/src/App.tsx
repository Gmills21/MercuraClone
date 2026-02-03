import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { TodayView } from './pages/TodayView';
import { Quotes } from './pages/Quotes';
import { SmartQuote } from './pages/SmartQuote';
import { QuoteReview } from './pages/QuoteReview';
import { QuoteView } from './pages/QuoteView';
import { Customers } from './pages/Customers';
import { Products } from './pages/Products';
import { Emails } from './pages/Emails';
import { CompetitorMapping } from './pages/CompetitorMapping';
import { QuickBooksIntegration } from './pages/QuickBooksIntegration';
import { AlertsPage } from './pages/AlertsPage';
import { CustomerIntelligence } from './pages/CustomerIntelligence';
import { IntelligenceDashboard } from './pages/IntelligenceDashboard';
import { CameraCapture } from './pages/CameraCapture';
import { BusinessImpact } from './pages/BusinessImpact';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { AccountBilling } from './pages/AccountBilling';
import { Security } from './pages/Security';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public route - no layout */}
        <Route path="/quote/:token" element={<QuoteView />} />

        {/* Protected routes - with layout */}
        <Route path="/" element={<Layout><TodayView /></Layout>} />
        <Route path="/emails" element={<Layout><Emails /></Layout>} />
        <Route path="/quotes" element={<Layout><Quotes /></Layout>} />
        <Route path="/quotes/new" element={<Layout><SmartQuote /></Layout>} />
        <Route path="/quotes/:id" element={<Layout><QuoteReview /></Layout>} />
        <Route path="/customers" element={<Layout><Customers /></Layout>} />
        <Route path="/products" element={<Layout><Products /></Layout>} />
        <Route path="/mappings" element={<Layout><CompetitorMapping /></Layout>} />
        <Route path="/quickbooks" element={<Layout><QuickBooksIntegration /></Layout>} />
        <Route path="/alerts" element={<Layout><AlertsPage /></Layout>} />
        <Route path="/intelligence" element={<Layout><IntelligenceDashboard /></Layout>} />
        <Route path="/intelligence/customers/:customerId" element={<Layout><CustomerIntelligence /></Layout>} />
        <Route path="/impact" element={<Layout><IntelligenceDashboard /></Layout>} />
        <Route path="/camera" element={<Layout><CameraCapture /></Layout>} />
        <Route path="/knowledge" element={<Layout><KnowledgeBasePage /></Layout>} />
        <Route path="/account/billing" element={<Layout><AccountBilling /></Layout>} />
        <Route path="/security" element={<Layout><Security /></Layout>} />
      </Routes>
    </Router>
  );
}

export default App;
