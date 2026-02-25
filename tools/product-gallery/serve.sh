#!/bin/bash
# SkyyRose Product Classifier — Dev Server
cd "$(dirname "$0")/../.."
echo ""
echo "  SkyyRose Product Classifier"
echo "  http://localhost:4200/tools/product-gallery/"
echo ""
python3 -m http.server 4200
