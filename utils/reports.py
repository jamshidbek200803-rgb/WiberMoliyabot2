import pandas as pd
import io
from datetime import datetime
from utils.i18n import get_text, get_cat_text

def create_excel_report(transactions, lang='uz'):
    """
    transactions: list of tuples (date, category_name, type, amount, comment)
    """
    if not transactions:
        return None
        
    # Convert to DataFrame
    df = pd.DataFrame(transactions, columns=[
        get_text('col_date', lang), 
        get_text('col_category', lang), 
        get_text('col_type', lang), 
        get_text('col_amount', lang), 
        get_text('col_comment', lang)
    ])
    
    # Format Category column
    cat_col = get_text('col_category', lang)
    df[cat_col] = df[cat_col].apply(lambda x: get_cat_text(x, lang))
    
    # Format 'Tur' column
    type_col = get_text('col_type', lang)
    df[type_col] = df[type_col].map({
        'income': get_text('type_income_label', lang), 
        'expense': get_text('type_expense_label', lang)
    })
    
    # Format 'Summa' column
    amount_col = get_text('col_amount', lang)
    sum_unit = get_text('sum', lang)
    df[amount_col] = df[amount_col].apply(lambda x: f"{x:,.0f} {sum_unit}")
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Hisobot', startrow=2)
        
        workbook = writer.book
        worksheet = writer.sheets['Hisobot']
        
        # Add title
        worksheet['A1'] = f"{get_text('report_header', lang)} ({datetime.now().strftime('%Y-%m-%d')})"
        
        # Auto-adjust column widths
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
            
    output.seek(0)
    return output
