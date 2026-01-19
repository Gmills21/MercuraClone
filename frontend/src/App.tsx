import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Quotes } from './pages/Quotes';
import { CreateQuote } from './pages/CreateQuote';
import { QuoteReview } from './pages/QuoteReview';
import { Customers } from './pages/Customers';
import { Products } from './pages/Products';
import { Emails } from './pages/Emails';
import { CompetitorMapping } from './pages/CompetitorMapping';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/emails" element={<Emails />} />
          <Route path="/quotes" element={<Quotes />} />
          <Route path="/quotes/new" element={<CreateQuote />} />
          <Route path="/quotes/:id" element={<QuoteReview />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/products" element={<Products />} />
          <Route path="/mappings" element={<CompetitorMapping />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
