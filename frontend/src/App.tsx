import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Quotes } from './pages/Quotes';
import { CreateQuote } from './pages/CreateQuote';
import { QuoteReview } from './pages/QuoteReview';
import { QuoteView } from './pages/QuoteView';
import { Customers } from './pages/Customers';
import { Products } from './pages/Products';
import { Emails } from './pages/Emails';
import { CompetitorMapping } from './pages/CompetitorMapping';

function App() {
  return (
    <Router>
      <Routes>
        {/* Public route - no layout */}
        <Route path="/quote/:token" element={<QuoteView />} />
        
        {/* Protected routes - with layout */}
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/emails" element={<Layout><Emails /></Layout>} />
        <Route path="/quotes" element={<Layout><Quotes /></Layout>} />
        <Route path="/quotes/new" element={<Layout><CreateQuote /></Layout>} />
        <Route path="/quotes/:id" element={<Layout><QuoteReview /></Layout>} />
        <Route path="/customers" element={<Layout><Customers /></Layout>} />
        <Route path="/products" element={<Layout><Products /></Layout>} />
        <Route path="/mappings" element={<Layout><CompetitorMapping /></Layout>} />
      </Routes>
    </Router>
  );
}

export default App;
