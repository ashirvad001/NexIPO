# IPO Intelligence Platform - Phase 2: Frontend

## 🎯 Overview
Phase 2 implements a modern, responsive Next.js frontend with TypeScript, Tailwind CSS, and interactive charts for IPO data visualization.

## 📁 Project Structure

```
frontend/
├── components/
│   ├── Layout.tsx              # Main layout with header/footer
│   ├── IPOCard.tsx             # IPO card component
│   ├── SubscriptionChart.tsx   # Bar chart for subscription data
│   ├── GMPChart.tsx            # Line chart for GMP trends
│   ├── Loading.tsx             # Loading spinner
│   └── Error.tsx               # Error display component
├── pages/
│   ├── _app.tsx                # Next.js app wrapper
│   ├── _document.tsx           # HTML document template
│   ├── index.tsx               # Dashboard/Home page
│   ├── active.tsx              # Active IPOs page
│   ├── upcoming.tsx            # Upcoming IPOs page
│   ├── ipos.tsx                # All IPOs with filters
│   └── ipo/
│       └── [id].tsx            # IPO detail page
├── services/
│   └── api.ts                  # API client with Axios
├── types/
│   └── ipo.ts                  # TypeScript interfaces
├── utils/
│   └── formatters.ts           # Utility functions
├── styles/
│   └── globals.css             # Global styles + Tailwind
├── public/                     # Static assets
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── tailwind.config.js          # Tailwind config
├── next.config.js              # Next.js config
└── .env.example                # Environment variables template
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on port 8000

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

The application will be available at: **http://localhost:3000**

## 📄 Pages

### 1. Dashboard (`/`)
- Overview of active and upcoming IPOs
- Quick stats
- Featured IPOs

### 2. Active IPOs (`/active`)
- List of currently open IPOs
- Real-time subscription data
- Days remaining countdown

### 3. Upcoming IPOs (`/upcoming`)
- Future IPO launches
- Timeline information
- Days until opening

### 4. All IPOs (`/ipos`)
- Complete IPO listing
- Advanced filters:
  - Status (upcoming, open, closed, listed)
  - Type (mainboard, SME)
  - Sector
  - Search (company name/symbol)
- Sorting options
- Pagination (12 per page)

### 5. IPO Detail (`/ipo/[id]`)
- Complete IPO information
- Subscription charts
- GMP trends
- Risk assessment (ML)
- Timeline
- Financial metrics

## 🎨 Components

### IPOCard
Reusable card component displaying:
- Company name and symbol
- Status badge
- Key metrics (price band, subscription, GMP)
- Countdown timers
- Risk score (if available)

**Props:**
```typescript
interface IPOCardProps {
  ipo: IPO;
}
```

### SubscriptionChart
Interactive bar chart showing:
- QIB (Qualified Institutional Buyers)
- NII (Non-Institutional Investors)
- Retail subscription

**Props:**
```typescript
interface SubscriptionChartProps {
  qib?: number | null;
  nii?: number | null;
  retail?: number | null;
}
```

### GMPChart
Line chart displaying:
- Price band range
- Estimated listing price
- GMP projection

**Props:**
```typescript
interface GMPChartProps {
  priceBandLower?: number | null;
  priceBandUpper?: number | null;
  gmpAmount?: number | null;
  estimatedListingPrice?: number | null;
}
```

### Layout
Main layout wrapper with:
- Responsive header with navigation
- Footer with links
- SEO meta tags

**Props:**
```typescript
interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}
```

## 🔌 API Integration

### API Service (`services/api.ts`)

```typescript
import { apiService } from '@/services/api';

// Get all IPOs with filters
const ipos = await apiService.getIPOs({
  page: 1,
  page_size: 20,
  status: 'open',
  sort_by: 'total_subscription',
  sort_order: 'desc'
});

// Get single IPO
const ipo = await apiService.getIPOById(1);

// Get active IPOs
const active = await apiService.getActiveIPOs();

// Get upcoming IPOs
const upcoming = await apiService.getUpcomingIPOs(10);
```

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## 🎨 Styling

### Tailwind CSS
Custom utility classes defined in `globals.css`:

```css
.card          /* White card with shadow */
.btn           /* Base button */
.btn-primary   /* Primary button */
.btn-secondary /* Secondary button */
.badge         /* Status badge */
.input         /* Form input */
.select        /* Select dropdown */
.spinner       /* Loading spinner */
```

### Color Palette

```javascript
primary:  #0ea5e9  // Blue
success:  #22c55e  // Green
danger:   #ef4444  // Red
warning:  #f59e0b  // Yellow
```

## 🛠️ Utility Functions

### Formatters (`utils/formatters.ts`)

```typescript
import {
  formatCurrency,      // ₹100.00
  formatCrores,        // ₹1000.50 Cr
  formatPercentage,    // 15.50%
  formatSubscription,  // 3.50x
  formatDate,          // 15 Jan 2024
  formatNumber,        // 1,00,000
  getStatusColor,      // Returns badge color class
  getRiskColor,        // Returns risk badge color
  getDaysUntil,        // Calculate days until date
} from '@/utils/formatters';
```

## 📊 Charts (Recharts)

Both charts are responsive and interactive:

```typescript
import SubscriptionChart from '@/components/SubscriptionChart';
import GMPChart from '@/components/GMPChart';

<SubscriptionChart 
  qib={2.5} 
  nii={1.8} 
  retail={3.2} 
/>

<GMPChart
  priceBandLower={280}
  priceBandUpper={295}
  gmpAmount={45}
  estimatedListingPrice={340}
/>
```

## 🔄 State Management

Using React hooks for state:

```typescript
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [data, setData] = useState<IPO[]>([]);

useEffect(() => {
  fetchData();
}, [dependencies]);
```

## 📱 Responsive Design

Breakpoints:
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px

Example usage:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```

## 🧪 Testing

### Manual Testing Checklist

- [ ] Dashboard loads with active/upcoming IPOs
- [ ] Navigation between pages works
- [ ] Filters on /ipos page work correctly
- [ ] Pagination functions properly
- [ ] Charts render with data
- [ ] IPO detail page shows all information
- [ ] Loading states display correctly
- [ ] Error states show appropriate messages
- [ ] Responsive design works on mobile
- [ ] Back button navigation works

### Test URLs

```bash
http://localhost:3000/           # Dashboard
http://localhost:3000/active     # Active IPOs
http://localhost:3000/upcoming   # Upcoming IPOs
http://localhost:3000/ipos       # All IPOs
http://localhost:3000/ipo/1      # IPO Detail
```

## 📦 Build & Deploy

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

## 🔧 Configuration Files

### next.config.js
- API proxy configuration
- Environment variables
- Build optimizations

### tailwind.config.js
- Custom color palette
- Extended theme
- Plugin configuration

### tsconfig.json
- TypeScript compiler options
- Path aliases (@/*)
- Strict type checking

## 🎯 Key Features Implemented

✅ **Responsive UI**
- Mobile-first design
- Tablet and desktop optimized
- Touch-friendly interactions

✅ **Interactive Charts**
- Subscription breakdown (Bar chart)
- GMP trends (Line chart)
- Tooltips and legends

✅ **Advanced Filtering**
- Status, type, sector filters
- Text search
- Sort by multiple fields
- Pagination

✅ **Real-time Data**
- Fetches from backend API
- Loading states
- Error handling
- Retry functionality

✅ **SEO Optimized**
- Meta tags
- Page titles
- Descriptions
- Semantic HTML

✅ **Performance**
- Code splitting
- Lazy loading
- Optimized images
- Fast page transitions

## 🐛 Troubleshooting

### API Connection Error
```bash
# Ensure backend is running
cd ../backend
uvicorn main:app --reload

# Check .env.local has correct API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :3000   # Windows
```

### Module Not Found
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors
```bash
# Check TypeScript errors
npm run type-check

# Clean build
rm -rf .next
npm run build
```

## 📈 Performance Optimization

### Implemented
- Next.js automatic code splitting
- Image optimization
- CSS purging with Tailwind
- Component lazy loading

### Future Improvements
- Implement React Query for caching
- Add service worker for offline support
- Optimize chart rendering
- Implement virtual scrolling for large lists

## 🎓 Interview Talking Points

### Architecture
> "I built a modern Next.js frontend with TypeScript for type safety. The application uses a component-based architecture with reusable UI components, centralized API service, and utility functions for data formatting."

### Responsive Design
> "I implemented mobile-first responsive design using Tailwind CSS. The layout adapts seamlessly from mobile (320px) to desktop (1920px+) with grid-based layouts and breakpoint-specific styling."

### Data Visualization
> "I integrated Recharts for interactive data visualization. The subscription chart uses bar charts to show category-wise data, while the GMP chart uses line charts to display price trends over time."

### User Experience
> "I focused on UX with loading states, error handling with retry options, empty states with helpful messages, and smooth page transitions. The filter system provides instant feedback and is mobile-friendly."

### Performance
> "The application leverages Next.js optimizations including automatic code splitting, lazy loading of components, and optimized image handling. API calls are properly cached and pagination prevents loading large datasets."

## 🔄 Integration with Phase 1

The frontend connects to the Phase 1 backend:

```typescript
API Base: http://localhost:8000/api/v1

Endpoints Used:
- GET /ipos/              # List with filters
- GET /ipos/{id}          # Detail
- GET /ipos/active        # Active IPOs
- GET /ipos/upcoming      # Upcoming IPOs
- GET /ipos/symbol/{sym}  # By symbol
```

## 📝 Next Steps (Phase 3)

- [ ] PDF prospectus upload
- [ ] File viewer component
- [ ] Upload progress tracking
- [ ] Document management UI

---

**Phase 2 Status**: ✅ Complete
**Current Progress**: 33.3% (10 of 30 days)
**Next Milestone**: File Ingestion (Phase 3)

Happy Coding! 🚀
